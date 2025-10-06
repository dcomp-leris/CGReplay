#!/usr/bin/env python3
# rtp_h264_depacketize.py
# Rebuild H.264 Annex-B from RTP (RFC 6184). Handles STAP-A/B (24/25), MTAP16/24 (26/27), FU-A/B (28/29), single NAL (1-23).
# Works with libpcap or pcapng inputs. Requires scapy (and scapy.contrib.rtp for header parsing).
# Usage:
#   python3 rtp_h264_depacketize.py --pcap v_ssrc_libpcap.pcap --ssrc 0xBB4F5B2E --pt 126 --out video.h264
#   (You can also pass the big Kombat_Washington.pcap; it will filter by SSRC/PT.)

import argparse, sys, struct
from collections import defaultdict, deque

try:
    from scapy.all import rdpcap, UDP, IP
    from scapy.contrib.rtp import RTP
except Exception as e:
    print("Please install scapy:  pip install scapy", file=sys.stderr)
    print("Error:", e, file=sys.stderr)
    sys.exit(1)

START_CODE = b"\x00\x00\x00\x01"

def u16(b, off): return struct.unpack_from("!H", b, off)[0]
def u24(b, off): 
    x = b[off:off+3]
    return (x[0]<<16)|(x[1]<<8)|x[2]

def write_nal(outf, nal):
    outf.write(START_CODE)
    outf.write(nal)

def parse_stap_a(payload, off, end, outf, sps_pps_store):
    # STAP-A: [STAP-A header already consumed] then: (len(16) | NAL)... repeated
    while off + 2 <= end:
        nlen = u16(payload, off); off += 2
        if nlen == 0 or off + nlen > end: break
        nal = payload[off:off+nlen]; off += nlen
        remember_sps_pps(nal, sps_pps_store)
        write_nal(outf, nal)
    return off

def parse_stap_b(payload, off, end, outf, sps_pps_store):
    # STAP-B: 16-bit DON first
    if off + 2 > end: return off
    _don = u16(payload, off); off += 2
    return parse_stap_a(payload, off, end, outf, sps_pps_store)

def parse_mtap16(payload, off, end, outf, sps_pps_store):
    # MTAP16: 16-bit DON, then repeated: 16-bit TS offset, 16-bit size, NAL
    if off + 2 > end: return off
    _don = u16(payload, off); off += 2
    while off + 4 <= end:
        _ts_off = u16(payload, off); off += 2
        nlen    = u16(payload, off); off += 2
        if nlen == 0 or off + nlen > end: break
        nal = payload[off:off+nlen]; off += nlen
        remember_sps_pps(nal, sps_pps_store)
        write_nal(outf, nal)
    return off

def parse_mtap24(payload, off, end, outf, sps_pps_store):
    # MTAP24: 16-bit DON, then repeated: 24-bit TS offset, 16-bit size, NAL
    if off + 2 > end: return off
    _don = u16(payload, off); off += 2
    while off + 5 <= end:
        _ts_off = u24(payload, off); off += 3
        nlen    = u16(payload, off); off += 2
        if nlen == 0 or off + nlen > end: break
        nal = payload[off:off+nlen]; off += nlen
        remember_sps_pps(nal, sps_pps_store)
        write_nal(outf, nal)
    return off

def remember_sps_pps(nal, store):
    if not nal: return
    nal_type = nal[0] & 0x1F
    if nal_type == 7 and store["sps"] is None:  # SPS
        store["sps"] = bytes(nal)
    elif nal_type == 8 and store["pps"] is None:  # PPS
        store["pps"] = bytes(nal)

def prepend_sps_pps_if_needed(outf, store, prepend_done):
    if not prepend_done[0]:
        if store["sps"] and store["pps"]:
            write_nal(outf, store["sps"])
            write_nal(outf, store["pps"])
            prepend_done[0] = True

def main():
    ap = argparse.ArgumentParser(description="Depacketize RTP/H.264 (incl. MTAP) to Annex-B .h264")
    ap.add_argument("--pcap", required=True, help="pcap/pcapng file")
    ap.add_argument("--ssrc", required=True, help="SSRC (e.g., 0xBB4F5B2E or decimal)")
    ap.add_argument("--pt", type=int, required=True, help="RTP payload type (e.g., 126)")
    ap.add_argument("--out", required=True, help="Output .h264 path")
    args = ap.parse_args()

    # Parse SSRC
    ssrc_str = args.ssrc.strip().lower()
    if ssrc_str.startswith("0x"):
        ssrc_val = int(ssrc_str, 16)
    else:
        ssrc_val = int(ssrc_str)

    pkts = rdpcap(args.pcap)
    # Buffer FU-A/B fragments: key by (timestamp, nal_type)
    fua_buf = {}

    sps_pps_store = {"sps": None, "pps": None}
    wrote_any = False
    prepend_done = [False]  # mutate by ref

    with open(args.out, "wb") as outf:
        # Iterate in capture order (already chronological)
        for p in pkts:
            if not p.haslayer(UDP): continue
            udp = p[UDP]
            raw = bytes(udp.payload)
            if len(raw) < 12: continue

            # Try RTP header parse (without scapy RTP layer to be robust to ext)
            # vpxccm: V=2 (bits 7-6), P(5), X(4), CC(3-0)
            vpxccm = raw[0]
            version = vpxccm >> 6
            if version != 2: continue
            has_ext = (raw[0] & 0x10) != 0
            csrc_count = (raw[0] & 0x0F)
            payload_type = raw[1] & 0x7F
            if payload_type != args.pt: continue

            seq = struct.unpack_from("!H", raw, 2)[0]
            timestamp = struct.unpack_from("!I", raw, 4)[0]
            ssrc = struct.unpack_from("!I", raw, 8)[0]
            if ssrc != ssrc_val: continue

            off = 12 + 4 * csrc_count
            if has_ext:
                if off + 4 > len(raw): continue
                # RTP header extension: 16-bit profile, 16-bit length (in 32-bit words)
                ext_len_words = struct.unpack_from("!H", raw, off+2)[0]
                off += 4 + 4 * ext_len_words

            if off >= len(raw): continue
            payload = raw[off:]
            if not payload: continue

            # H.264 NAL parsing
            if len(payload) < 1: continue
            nal0 = payload[0]
            nal_type = nal0 & 0x1F

            # Before writing the first IDR, try to prepend SPS/PPS once we have them
            if nal_type in (5, 1):  # IDR or non-IDR slice
                prepend_sps_pps_if_needed(outf, sps_pps_store, prepend_done)

            if 1 <= nal_type <= 23:
                # Single NAL
                remember_sps_pps(payload, sps_pps_store)
                write_nal(outf, payload)
                wrote_any = True

            elif nal_type == 24:
                # STAP-A: skip header (1B)
                parse_stap_a(payload, 1, len(payload), outf, sps_pps_store)
                wrote_any = True

            elif nal_type == 25:
                # STAP-B
                parse_stap_b(payload, 1, len(payload), outf, sps_pps_store)
                wrote_any = True

            elif nal_type == 26:
                # MTAP16
                parse_mtap16(payload, 1, len(payload), outf, sps_pps_store)
                wrote_any = True

            elif nal_type == 27:
                # MTAP24
                parse_mtap24(payload, 1, len(payload), outf, sps_pps_store)
                wrote_any = True

            elif nal_type in (28, 29):
                # FU-A or FU-B
                if len(payload) < 2: continue
                fu_ind = payload[0]   # F | NRI | 11100
                fu_hdr = payload[1]   # S | E | R | Type(5)
                S = (fu_hdr & 0x80) != 0
                E = (fu_hdr & 0x40) != 0
                T = fu_hdr & 0x1F
                F = (fu_ind & 0x80)
                NRI = (fu_ind & 0x60)

                pos = 2
                if nal_type == 29:
                    # FU-B carries 16-bit DON after FU header
                    if len(payload) < 4: continue
                    _don = u16(payload, 2); pos = 4

                key = (timestamp, T)
                if S:
                    # start: create reconstructed NAL header
                    nal_header = bytes([F | NRI | T])
                    fua_buf[key] = bytearray()
                    fua_buf[key] += nal_header
                    fua_buf[key] += payload[pos:]
                else:
                    if key not in fua_buf:
                        # missing start; skip
                        continue
                    fua_buf[key] += payload[pos:]

                if E and key in fua_buf:
                    nal = bytes(fua_buf.pop(key))
                    remember_sps_pps(nal, sps_pps_store)
                    # Before first IDR slice, ensure SPS/PPS are written
                    if (nal[0] & 0x1F) in (5, 1):
                        prepend_sps_pps_if_needed(outf, sps_pps_store, prepend_done)
                    write_nal(outf, nal)
                    wrote_any = True

            else:
                # Unsupported / reserved type, skip
                continue

    if not wrote_any:
        print("No H.264 NALs were written. Check SSRC/PT, or encryption (SRTP/DTLS).", file=sys.stderr)
        sys.exit(2)

    print(f"Done. Wrote Annex-B bitstream to: {args.out}")
    print("Next: mux to MP4")
    print(f"  ffmpeg -r 30 -i {args.out} -c copy out_h264.mp4 || ffmpeg -r 30 -i {args.out} -c:v libx264 -pix_fmt yuv420p out_h264.mp4")

if __name__ == "__main__":
    main()

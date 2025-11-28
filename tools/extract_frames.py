#!/usr/bin/env python3
from scapy.all import *
import os
import subprocess
import tempfile
import argparse
from collections import defaultdict


class RTPVideoExtractor:
    def __init__(self, input_pcap, output_file=None, codec="h264"):
        """
        Initialize the RTP video extractor.
        
        Args:
            input_pcap (str): Path to the input PCAP file
            output_file (str): Path to the output video file (default: output.mp4)
            codec (str): Video codec ('h264' or 'h265')
        """
        self.input_pcap = input_pcap
        self.codec = codec.lower()
        
        if output_file is None:
            output_file = f"output.{self.get_extension()}"
        self.output_file = output_file
        
        # Temporary file to store raw NAL units
        self.temp_raw_file = tempfile.NamedTemporaryFile(
            delete=False, 
            suffix=f".{'h264' if self.codec == 'h264' else 'hevc'}"
        ).name
        
    def get_extension(self):
        """Get the appropriate file extension based on codec."""
        return "mp4"  # MP4 container works for both H.264 and H.265

    def process_pcap(self):
        """Extract RTP packets from PCAP and rebuild the video stream."""
        print(f"Reading packets from {self.input_pcap}...")
        
        try:
            packets = rdpcap(self.input_pcap)
        except Exception as e:
            print(f"Error reading PCAP file: {e}")
            return False
        
        print(f"Found {len(packets)} packets in the PCAP file")
        
        rtp_packets = {}
        
        # Extract RTP packets keyed by sequence number for sorting
        for packet in packets:
            if UDP in packet and Raw in packet:
                udp_payload = bytes(packet[Raw])
                if len(udp_payload) >= 12 and (udp_payload[0] >> 6) == 2:
                    # Parse RTP header
                    cc = udp_payload[0] & 0x0F
                    header_size = 12 + 4 * cc
                    extension = (udp_payload[0] >> 4) & 0x1
                    
                    # Handle RTP header extensions
                    if extension and len(udp_payload) >= header_size + 4:
                        ext_len = (udp_payload[header_size+2] << 8) | udp_payload[header_size+3]
                        header_size += 4 + 4 * ext_len
                    
                    if len(udp_payload) > header_size:
                        seq = (udp_payload[2] << 8) | udp_payload[3]
                        marker = (udp_payload[1] >> 7) & 0x1
                        payload_type = udp_payload[1] & 0x7F
                        timestamp = (udp_payload[4] << 24) | (udp_payload[5] << 16) | (udp_payload[6] << 8) | udp_payload[7]
                        payload = udp_payload[header_size:]
                        
                        # Filter only video RTP packets (payload type 96)
                        if payload_type == 96:
                            rtp_packets[seq] = {
                                'payload': payload, 
                                'marker': marker, 
                                'timestamp': timestamp
                            }
        
        if not rtp_packets:
            print("No video RTP packets found in the PCAP file")
            return False
        
        print(f"Found {len(rtp_packets)} video RTP packets")
        
        # Reconstruct NAL units from RTP packets
        nal_units = self.reconstruct_nal_units(rtp_packets)
        
        if not nal_units:
            print("No NAL units could be reconstructed")
            return False
        
        # Write all NAL units to the temporary file
        with open(self.temp_raw_file, 'wb') as f:
            for nal in nal_units:
                f.write(nal)
        
        print(f"Extracted {len(nal_units)} NAL units to {self.temp_raw_file}")
        
        # Convert raw NAL units to output video file using ffmpeg
        return self.convert_to_video()

    def reconstruct_nal_units(self, rtp_packets):
        """
        Reconstruct NAL units from RTP packets, handling fragmentation.
        
        Args:
            rtp_packets (dict): Dictionary of RTP packets keyed by sequence number
            
        Returns:
            list: List of complete NAL units with start codes
        """
        nal_units = []
        fragments = {}  # key: start_seq, value: list of payload parts for FU reassembly
        fu_start_seq = None  # track current FU-A start sequence
        
        # Process packets in sequence order
        sorted_seq_nums = sorted(rtp_packets.keys())
        
        for seq in sorted_seq_nums:
            pkt = rtp_packets[seq]
            payload = pkt['payload']
            marker = pkt['marker']
            timestamp = pkt['timestamp']
            
            if len(payload) < 1:
                continue
            
            if self.codec == "h264":
                nal_unit_type = payload[0] & 0x1F
                
                if nal_unit_type >= 1 and nal_unit_type <= 23:
                    # Single NAL unit packet
                    nal_units.append(b'\x00\x00\x00\x01' + payload)
                
                elif nal_unit_type == 28 and len(payload) >= 2:
                    # FU-A fragmentation unit
                    fu_header = payload[1]
                    start_bit = (fu_header >> 7) & 0x1
                    end_bit = (fu_header >> 6) & 0x1
                    original_nal_type = fu_header & 0x1F
                    
                    if start_bit:
                        # Start new fragment
                        fu_start_seq = seq
                        # Rebuild NAL header for the FU
                        nal_header = bytes([(payload[0] & 0xE0) | original_nal_type])
                        fragments[fu_start_seq] = [nal_header + payload[2:]]
                    elif fu_start_seq is not None and fu_start_seq in fragments:
                        # Middle or end fragment
                        fragments[fu_start_seq].append(payload[2:])
                        
                        if end_bit:
                            # Reassemble FU-A NAL unit
                            nal_data = b''.join(fragments[fu_start_seq])
                            nal_units.append(b'\x00\x00\x00\x01' + nal_data)
                            del fragments[fu_start_seq]
                            fu_start_seq = None
                
                elif nal_unit_type == 24:
                    # STAP-A aggregation packet
                    offset = 1
                    while offset < len(payload):
                        if offset + 2 > len(payload):
                            break
                        size = (payload[offset] << 8) | payload[offset + 1]
                        offset += 2
                        if offset + size <= len(payload):
                            nal_units.append(b'\x00\x00\x00\x01' + payload[offset:offset+size])
                            offset += size
                        else:
                            break
            
            elif self.codec == "h265":
                nal_unit_type = (payload[0] >> 1) & 0x3F
                
                if nal_unit_type < 48:
                    # Single NAL unit
                    nal_units.append(b'\x00\x00\x00\x01' + payload)
                
                elif nal_unit_type == 49 and len(payload) >= 3:
                    # FU fragmentation unit for H265
                    fu_header = payload[2]
                    start_bit = (fu_header >> 7) & 0x1
                    end_bit = (fu_header >> 6) & 0x1
                    original_nal_type = fu_header & 0x3F
                    
                    if start_bit:
                        fu_start_seq = seq
                        # Compose reconstructed NAL header
                        nal_header_first_byte = (payload[0] & 0x81) | (original_nal_type << 1)
                        nal_header = bytes([nal_header_first_byte]) + payload[1:2]
                        fragments[fu_start_seq] = [nal_header + payload[3:]]
                    elif fu_start_seq is not None and fu_start_seq in fragments:
                        fragments[fu_start_seq].append(payload[3:])
                        
                        if end_bit:
                            nal_data = b''.join(fragments[fu_start_seq])
                            nal_units.append(b'\x00\x00\x00\x01' + nal_data)
                            del fragments[fu_start_seq]
                            fu_start_seq = None
        
        # Flush any remaining fragmented units (incomplete ones)
        for start_seq, parts in fragments.items():
            if parts:
                nal_data = b''.join(parts)
                nal_units.append(b'\x00\x00\x00\x01' + nal_data)
        
        return nal_units
    
    def convert_to_video(self):
        """
        Convert the raw NAL units to a playable video file using FFmpeg.
        
        Returns:
            bool: True if conversion was successful, False otherwise
        """
        print(f"Converting raw {self.codec} data to {self.output_file}...")
        
        try:
            cmd = [
                "ffmpeg", "-y",
                "-loglevel", "error",
                "-i", self.temp_raw_file,
                "-c:v", "copy",
                self.output_file
            ]
            
            process = subprocess.run(cmd, check=True)
            print(f"Successfully converted video to {self.output_file}")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"Error converting video: {e}")
            return False
        finally:
            # Clean up the temporary file
            if os.path.exists(self.temp_raw_file):
               os.remove(self.temp_raw_file)


def main():
    parser = argparse.ArgumentParser(description="Extract video from RTP packets in a PCAP file")
    parser.add_argument("input_pcap", default = "rtp_stream_h264.pcap", help="Input PCAP file ,default: rtp_stream_h264.pcap")
    parser.add_argument("-o", "--output", default = "output.mp4", help="Output video file, default: output.mp4")
    parser.add_argument("-c", "--codec", choices=["h264", "h265"], default="h264",
                        help="Video codec (default: h264)")
    
    args = parser.parse_args()
    
    extractor = RTPVideoExtractor(
        input_pcap=args.input_pcap,
        output_file=args.output,
        codec=args.codec
    )
    
    success = extractor.process_pcap()
    if success:
        print("Video extraction completed successfully!")
    else:
        print("Video extraction failed.")


if __name__ == "__main__":
    main()
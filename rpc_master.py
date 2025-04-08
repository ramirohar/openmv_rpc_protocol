import io,struct, rpc, time
from PIL import Image
import numpy as np

RPC_OK = struct.pack("<I", 0)
RPC_ERROR = struct.pack("<I", 1)
RPC_WRONG_ARGUMENTS = struct.pack("<I", 2)
RPC_EMPTY_IMAGE = struct.pack("<I", 3)
RPC_FAILED_SNAPSHOT = struct.pack("<I", 4)


def check_status(result):
    
    if result is None:
        raise Exception("Return message is empty")
    
    status, = struct.unpack("<I", result[:4])
    
    if status != 0:
        raise Exception(f"RPC Error: {status}")

    return result[4:]    
    

def call_and_check(interface, *args, **kwargs):
    result = interface.call(*args, **kwargs)
    
    return check_status(result)

#####################


def jpeg_image_snapshot(interface):
    result = call_and_check(interface, "rpc_jpeg_image_snapshot")
    
    size, = struct.unpack("<I", result)    
    img = bytearray(size)
    
    return img

def set_exposure(interface, exposure_time):
    status_result = call_and_check(interface, "rpc_set_exposure", struct.pack("<I", exposure_time))
    time.sleep(2)

def set_framesize(interface, framesize):
    status_result = call_and_check(interface, "rpc_set_framesize", framesize.encode())
    
def set_pixelformat(interface, pixelformat):
    status_result = call_and_check(interface, "rpc_set_pixelformat",  pixelformat.encode())

def read_fb_chunk(interface, offset, max_chunk_size, out, *, retries=3):
    rpc_args = struct.pack("<II", offset, max_chunk_size)
    for _ in range(retries):
        try:
            result = call_and_check(interface, "rpc_read_fb_chunk", rpc_args)
            print(len(result))
            chunk_size = len(result)
            
            assert chunk_size <= max_chunk_size
            assert offset+chunk_size <= len(out)
            
            out[offset:offset+chunk_size] = result # Write the image data.
            
            break
        except Exception as ex:
            print(ex)
    else:
        print(f"Failed after {retries} retries")
        
        
class Camara:
    def __init__(self, port):
        self.interface1 = rpc.rpc_usb_vcp_master(port=port)
        
        # self.set_pixformat_framesize("sensor.GRAYSCALE", "sensor.VGA")
            
    def get_frame_buffer_call_back(self, pixformat_str, framesize_str):
    
        set_framesize(self.interface1, "sensor.VGA")
        
        set_pixelformat(self.interface1, "sensor.GRAYSCALE")
        
        img = jpeg_image_snapshot(self.interface1)
        # Transfer 32 KB chunks.
        chunk_size = (1 << 15)

        for offset in range(0, len(img), chunk_size):
            print(f"Reading {chunk_size} bytes starting at {offset}")
            read_fb_chunk(self.interface1, offset, chunk_size, img)
            
        return img
    
    
    def set_exposure(self, exposure_time):
        set_exposure(self.interface1, exposure_time)
        
        
    def get_snapshot(self, path,cutthrough=True):
        data = self.get_frame_buffer_call_back("sensor.GRAYSCALE", "sensor.VGA")
        print(len(data))
        
        if data:
            return data
        else:
            print("Error")






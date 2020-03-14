"""
SmartScope 
Common utility functions and classes.

Duke University - 2019
Licensed under the MIT License (see LICENSE for details)
Written by Caleb Sanford
"""


####################################################
# Change these lines to import different camera package
####################################################
import cv2
import numpy as np
import subprocess

def start_cam():
    ''' Initializes the PVCAM

    returns: cam instance
    '''
    try:
        cam = cv2.VideoCapture(0)
        if cam.isOpened(): # try to get the first frame
            rval, frame =  cam.read()
        subprocess.call(['DN_DS_Ctrl.exe', 'AXILevel', '6'])
    except:
        raise RuntimeError('Could not start Camera')
    return cam

def get_frame_size():
    '''
    returns a tuple (<image pixel width>, <image pixel height>)
    '''
    cam = start_cam()
    rval, frame = cam.read()
    height, width, _ = frame.shape
    close_cam(cam)
    return (width, height)

def close_cam(cam):
    ''' Closes the PVCAM instance
    args:
        - camera instance 
    '''
    try:
        cam.release()
    except:
        print_error('Could not close Camera')

def get_frame(exposure):
    ''' Gets a frame from the camera '''
    cam = start_cam()
    _, frame = cam.read()
    close_cam(cam)
    return frame

def get_live_frame(cam, exposure):
    ''' Gets a frame from the passed camera instance. This is a faster 
    way to get consecutive frames from a camera, used for focus and 
    imaging.

    args:
        - cam: camera instance 
        - exposure: exposure time

    '''
    _, frame = cam.read()
    return frame

####################################################
# To use an XYZ controller other than micro-manager,
# change the following lines to fit your stages
####################################################
import serial

def get_stage_controller(COM_port):
    ''' Gets an instance of the stage controller (micro-manager).
    This function can be changed to return other python controllers.
    '''
    return serial.Serial(COM_port, 9600, timeout=5)

def get_x_pos(stage_controller):
    message = "get x".encode()
    stage_controller.write(message)
    return float(stage_controller.readline())

def get_y_pos(stage_controller):
    message = "get y".encode()
    stage_controller.write(message)
    return float(stage_controller.readline())

def get_z_pos(stage_controller):
    message = "get z".encode()
    stage_controller.write(message)
    return float(stage_controller.readline())

def set_xy_pos(stage_controller, x, y):
    stage_controller.write("moveXY "+str(x)+" "+str(y))
    return stage_controller.readline()

def set_z_pos(stage_controller, z):
    stage_controller.write("moveZ "+str(z))
    return stage_controller.readline()

def wait_for_system(stage_controller):
    pass
 
# LED and Shutter Control
# Uncomment the following lines for manual control and be sure to comment 
# out the corresponding autocontrol functions:
'''
def change_shutter(controller, value):
    input ('Change shutter to: '+ value + ' then press Enter')
    
def change_LED_values(controller, LED, value):
    input ('Change LED values to match: LED: ' + LED + ' value: '+ value + ' then press Enter')
'''
# AUTO CONTROL FUNCTIONS
def change_shutter(controller, value):
    # controller.setProperty('IL-Turret', 'State', value)
    pass
    
def change_LED_values(controller, LED, value):
    # if controller.getProperty('Thorlabs DC4100', 'Operation Mode') != 'Brightness Mode':
    #     print ( controller.getProperty('Thorlabs DC4100', 'Operation Mode'))
    #     controller.setProperty('Thorlabs DC4100', 'Operation Mode', 'Brightness Mode')
    # port = controller.getProperty('Thorlabs DC4100', 'Port')
    # if value != 0:
    #     on_off = "1"
    #     controller.setProperty('Thorlabs DC4100', 'Percental Brightness LED-'+str(LED), value)
    #     controller.setSerialPortCommand(port, bytearray.fromhex("4F203" + str(LED-1) + "203" + on_off + "0A453F0A").decode(), "")
    # else:
    #     on_off = "0"
    #     controller.setSerialPortCommand(port, bytearray.fromhex("4F203" + str(LED-1) + "203" + on_off + "0A453F0A").decode(), "")
    #     controller.setProperty('Thorlabs DC4100', 'Percental Brightness LED-'+str(LED), value)
    pass
#################################################################

def set_LEDs_off(controller):
    change_LED_values(controller, 1, 0)
    change_LED_values(controller, 2, 0)
    change_LED_values(controller, 3, 0)
    change_LED_values(controller, 4, 0)

def set_led_and_shutter(controller, val):
    for k, v in val.items():
        if k == 'shutter':
            change_shutter(controller, v)
        else:
            change_LED_values(controller, k, v)

####################################################
# General hardware control
####################################################
def before_imaging():
    ''' This function runs when the start button is pressed '''
    pass

def before_every_image():
    ''' This function runs once directly before each image is taken '''
    pass

def after_every_image():
    ''' This function runs once directly after each image is taken '''
    pass

def after_imaging():
    ''' This function runs when the entire imaging process is complete '''
    pass

def in_between_channels():
    ''' This function runs in between different imaging channels if more that one 
        is selected 
    '''
    pass

####################################################
# Image manipulation 
####################################################
from numba import autojit
import numpy as np

@autojit
def convert_frame_to_mrcnn_format(frame):
    ''' Converts the output from the PVCAM frame 
    into the format that the mrcnn model was trained on

    args:
        frame: frame output from PVCAM
    returns:
        frame in mrcnn fromat
    '''
    new_im = np.zeros((frame.shape[0], frame.shape[1], 3))
    frame = bytescale(frame, high=255)
    for ix, iy in np.ndindex(frame.shape):
        val = frame[ix,iy]
        new_im[ix,iy] = [val,val,val]
    new_im = new_im.astype('uint8')
    return new_im

@autojit
def bytescale(data, current_min=0, current_max=None, high=65535, low=0):
    ''' Scales 2D pixel values from a camera to the specified high and 
        low values
    args: 
        data: frame array from camera (grayscale values)
        current_min: the min value of the raw pixel values 
        current_max: the max value of the raw pixel values. This 
                will usually be 255 (8-bit) or 16383 (14-bit)
        high: the high value to scale to (65535 for 16-bit)
        low: the low value to scale to
    
    returns:
        2D 16-bit depth array
    '''
    if current_min is None:
        current_min = data.min()
    if current_max is None:
        current_max = data.max()

    cscale = current_max - current_min
    if cscale < 0:
        raise ValueError("`current_max` should be larger than `current_min`.")
    elif cscale == 0:
        cscale = 1

    scale = float(high - low) / cscale
    bytedata = (data - current_min) * scale + low

    if high == 65535:
        return (bytedata.clip(low, high) + 0.5).astype('uint16')
    elif high == 255:
        return (bytedata.clip(low, high) + 0.5).astype('uint8')
    else:
        return (bytedata.clip(low, high) + 0.5)

####################################################
# Scope Calibration 
####################################################

def get_stage_to_pixel_ratio(stage_point_1, stage_point_2, 
                             pixel_val_1, pixel_val_2):
    ''' Calculates how many microns are in one pixel
    args:
        stage_point_1: xy StagePosition instance
        stage_point_2: xy StagePosition instance
        pixel_val_1: camera pixel value (x,y)
        pixel_val_2: camera pixel value (x,y)
    returns:
        float
    '''
    stage_distance_x = np.abs(stage_point_1.x - stage_point_2.x)
    stage_distance_y = np.abs(stage_point_1.y - stage_point_2.y)
    pixel_distance_x = np.abs(pixel_val_1[0] - pixel_val_2[0])
    pixel_distance_y = np.abs(pixel_val_1[1] - pixel_val_2[1])

    stage_pixel_ratio_x = float(stage_distance_x) / float(pixel_distance_x)
    stage_pixel_ratio_y = float(stage_distance_y) / float(pixel_distance_y)

    return (stage_pixel_ratio_x + stage_pixel_ratio_y) / 2
    
####################################################
# Printing
####################################################

def print_info(message):
    print ('[SS INFO]:'+ message)

def print_error(message):
    print('------------------------------------------------------')
    print ('[SS ERROR]:'+ message)
    print('------------------------------------------------------')
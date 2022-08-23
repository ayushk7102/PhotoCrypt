import cv2 as cv
import random
import math
import numpy as np
from img_encrypt import conv_bin, conv_dec

class photo_decoder:
	def __init__(self):
		self.IMG_SIZE = 250
		self.IMG_PATH = ''
		self.color_space = 'bgr'
		self.num_channels = 3

		self.img_crypt = None
		self.msg = ''

		self.i_offset = 0
		self.num_pairs = 0

	def read_image(self):
		img_path = '/home/ayush/Desktop/Stuff/Random/PhotoCrypt/PhotoCrypt/lena_encrypted.jpeg'
		self.img_crypt = cv.imread(img_path)
		

	def decode_metadata(self):
		# Reverse LSB-encoded in the last n bytes of the image
		# where n = ceil( log2(IMG_SIZE^2 * num_channels) )
		# <number_of_bit_pairs> <offset_index> 

		n_bits = math.ceil(math.log2((self.IMG_SIZE**2) * self.num_channels))
		print('n_bits required: ', n_bits)
		# exit()
		if self.color_space == 'bgr':
			b, g, r = self.img_crypt[:, :, 0], self.img_crypt[:, :,1], self.img_crypt[:, :, 2]
			img_stacked = np.concatenate((b, g, r), axis=0)
			
			flat = img_stacked.flatten()
			rev_flat = list(flat)[::-1]
			print(rev_flat)
			exit()
			
			bitstr_off = ''
			bitstr_pairs = ''
			
			for i in range(n_bits):
				if i < n_bits // 2:
					bitstr_off += conv_bin(rev_flat[i], 8)[6:]
				else:
					bitstr_pairs += conv_bin(rev_flat[i], 8)[6:]

			self.i_offset = conv_dec(bitstr_off)
			self.num_pairs = conv_dec(bitstr_pairs)
			print('i_offset = ', self.i_offset)
			print('num_pairs = ', self.num_pairs)



if __name__ == '__main__':
	p = photo_decoder()
	p.read_image()
	p.decode_metadata()
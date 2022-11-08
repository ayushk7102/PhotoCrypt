import cv2 as cv
import random
import math
import numpy as np

import os
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

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
		self.flat = None

	def read_image(self):
		img_path = '/home/ayush/Desktop/Stuff/Random/PhotoCrypt/PhotoCrypt/lena_encrypted.png'
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
			
			self.flat = img_stacked.flatten()

			# print(rev_flat)
			# exit()
			
			bitstr_off = ''
			bitstr_pairs = ''

			i = self.flat.shape[0]-1
			idx = 0

			for count in range(n_bits//2):
				pix = self.flat[i]
				# print(i,':',flat[i], ' ', conv_bin(pix, 8)[6:])
				bitstr_off += conv_bin(pix, 8)[6:]
				i-=1


			for count in range(n_bits//2):
				pix = self.flat[i]
				# print(i,':',flat[i], ' ', conv_bin(pix, 8)[6:])
				bitstr_pairs += conv_bin(pix, 8)[6:]
				i-=1		

			print(bitstr_off)
			self.i_offset = conv_dec(bitstr_off)
			self.num_pairs = conv_dec(bitstr_pairs)
			print('i_offset = ', self.i_offset)
			print('num_pairs = ', self.num_pairs)

	def decrypt_msg(self, ct):
		encoding = 'utf-8'
		with open('key.txt', 'rb') as f:
			key = f.read()

		with open('iv.txt', 'rb') as f:
			iv = f.read()

		cipher = Cipher(algorithms.AES(key), modes.CBC(iv))

		decryptor = cipher.decryptor()

		x = decryptor.update(ct) + decryptor.finalize()
		print(x)
		return x
	

	def decode_msg(self, encrypted=False):

		i_off = self.i_offset
		n_pairs = self.num_pairs

		bitstream = ''
		curr_bits = ''
		message = ''
		count_bits = 0
		byte_arr = []
		for i in range(i_off, i_off+n_pairs):
			pix = self.flat[i]
			bin_pix = conv_bin(pix, 8)
			bitstream += bin_pix[6:]
			curr_bits += bin_pix[6:]
			count_bits+=2

			if(count_bits == 8):
				if not encrypted:
					message += chr(int(curr_bits, 2))
				else:
					byte_arr.append(int(curr_bits, 2))
				count_bits = 0
				curr_bits= ''
		# print(bitstream)
		# print(byte_arr)
		# print(bytearray(byte_arr))
		message = (self.decrypt_msg(bytearray(byte_arr)))
		print('msg= ',message)


if __name__ == '__main__':
	encrypted = True
	p = photo_decoder()
	p.read_image()
	p.decode_metadata()
	p.decode_msg(encrypted)



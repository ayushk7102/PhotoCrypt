import cv2 as cv
import random
import math
import numpy as np
import os
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

def conv_bin(n, max_num):
    b = ''
    n = int(n)
    count = 0
    while(n >=2):
        b=str(n%2)+b
        n = n//2
    b = str(n) + b
    count = len(b)

    for i in range(count, max_num):
        b = '0' + b    
    
    return b

def conv_dec(bin_str):
	m = 0
	count = 0
	for i in bin_str[::-1]:
		num = int(i)
		m += num*(2**count)
		count+=1
	return m

class photo_encoder:

	def __init__(self):
		self.IMG_SIZE = 250
		self.IMG_PATH = ''
		self.color_space = 'bgr'
		self.num_channels = 3

		self.img = None
		self.img_crypt = None
		self.msg = ''
		self.crypt_dict = {}

		self.visualise = False
		self.save_img = True 

	def read_image(self):
		img_path = '/home/ayush/Desktop/Stuff/Random/PhotoCrypt/PhotoCrypt/lena.jpeg'
		self.img = cv.resize(cv.imread(img_path), (self.IMG_SIZE, self.IMG_SIZE))
		# cv.imshow('sfa', self.img)
		# cv.waitKey(0)
		# cv.destroyAllWindows()

	#returns a string containing message in binary
	def binarise_message(self, msg, encrypted=False):
		bitstream = ''
		if encrypted:
			for byte in msg:
				bitstream += (f'{byte:0>8b}')			

		if not encrypted:
			msg_len = len(msg)
			print('Length of message: ', msg_len, ' chars')
			print('({0} bits)'.format((msg_len)*8))
			
			for j in msg:
				bitstream += conv_bin(ord(j), 8)

		return bitstream

	def get_crypt_dict(self, bin_msg):
		#dict with random number pixel offset, number of bit pairs, and bitstream
		
		crypt_dict = {}
		# for j in range(0, len(bin_msg)-1, 2):
			# print('Pair {0}: {1}{2}'.format(j//2, bin_msg[j], bin_msg[j+1]))

		crypt_dict['offset'] = random.randint(0, self.IMG_SIZE * self.IMG_SIZE * self.num_channels - len(bin_msg)//2)
		crypt_dict['num_pairs'] = len(bin_msg)//2
		crypt_dict['bitstream'] = bin_msg

		# print(crypt_dict)
		self.crypt_dict = crypt_dict

	def encryptor(self, msg):

		def padding(msg): # needed to have message size divisible by 16 (block length)
			mlen = len(msg)
			while(mlen % 16 != 0):
				msg += '0'
				mlen += 1
			return msg

		msg = padding(msg)
		key = os.getrandom(32)
		iv = os.getrandom(16)

		# print('key = ',key)
		# print('iv = ', iv)
		cipher = Cipher(algorithms.AES(key), modes.CBC(iv))

		encryptor = cipher.encryptor()

		# pt = b"a secret message"
		pt = str.encode(msg)
		ct = encryptor.update(pt) + encryptor.finalize()
		# print('ct=',ct)

		for my_byte in ct:
			print(f'{my_byte:0>8b}', end=' ')

		with open('key.txt', 'wb') as f:
			f.write(key)

		with open('iv.txt', 'wb') as f:
			f.write(iv)

		return ct		

	def encode_image(self):
		crypt_dict = self.crypt_dict

		if self.color_space == 'bgr':
			b, g, r = self.img[:, :, 0], self.img[:, :,1], self.img[:, :, 2]
			img_stacked = np.concatenate((b, g, r), axis=0)
			# cv.imshow('asd', img_stacked)
			# cv.waitKey(0)
			# cv.destroyAllWindows()
			# print(img_stacked.shape)

			i_off = self.crypt_dict['offset']


			flat = (img_stacked.flatten())
			bitstream = self.crypt_dict['bitstream']
			idx = 0

			#encoding the message in flattened pixel array
			for i in range(i_off, i_off+crypt_dict['num_pairs']):
				# print()
				pix = flat[i]
				bin_pix = conv_bin(pix, 8)

				bin_pix_short = bin_pix[:len(bin_pix) - 2]

				# print(conv_bin(pix, 8), end=' ')
				# print('bin_pix_short: ',bin_pix_short,end=' ')


				flat[i] = conv_dec(bin_pix_short + bitstream[idx:idx+2])
				idx+=2



			# Reverse LSB-encoding the metadata in the last n bytes of the image
			# where n = ceil( log2(IMG_SIZE^2 * num_channels) )
			# <number_of_bit_pairs> <offset_index> 

			n_bits = math.ceil(math.log2((self.IMG_SIZE**2) * self.num_channels))
			# print('n_bits required: ', n_bits)
			
			offset_bin = conv_bin(i_off, n_bits)
			size_bin = conv_bin(crypt_dict['num_pairs'], n_bits)
			# print(('offset: '+ offset_bin, 'size :'+ size_bin))
			
			# print('i_offset = ', i_off)
			# print('num_pairs = ',crypt_dict['num_pairs'])
			#encoding the offset index in the last n pixels, in reverse

			i = flat.shape[0]-1
			idx = 0
			# print('i at start of encoding offset: ', i)
			for count in range(n_bits//2):
				pix = flat[i]
				bin_pix = conv_bin(pix, 8)
				bin_pix_short = bin_pix[:len(bin_pix) - 2]
				flat[i] = conv_dec(bin_pix_short + offset_bin[idx:idx+2])
				
				# print('previously flat[{0}]={1} ({2})'.format(i, flat[i], bin_pix))
				# print('now flat[{0}]={1} ({2})'.format(i, flat[i], bin_pix_short + offset_bin[idx:idx+2]))
				# print(i, ': ', offset_bin[idx:idx+2] )

				idx+=2
				i-=1


			idx = 0
			# i = flat.shape[0]- n_bits - 2
			

			#encoding the number of pairs in the previous n pixels, in reverse
			for count in range(n_bits//2):

				pix = flat[i]
				bin_pix = conv_bin(pix, 8)
				bin_pix_short = bin_pix[:len(bin_pix) - 2]

				# print('previously flat[{0}]={1}'.format(i, flat[i]))
				flat[i] = conv_dec(bin_pix_short + size_bin[idx:idx+2])
				# print('now flat[{0}]={1}'.format(i, flat[i]))
				# print(i, ': ', size_bin[idx:idx+2] )

				idx+=2
				i-=1

			
			reshaped = np.zeros_like(self.img)
			count = 0
			for i in range(self.num_channels):
				for r in range(self.IMG_SIZE):
					for c in range(self.IMG_SIZE):
						reshaped[r, c, i] = flat[count]
						count+=1
			print(self.img.shape)
			print(reshaped.shape)
			self.img_crypt = reshaped

			if self.visualise: 
				self.metric_vis()

			if self.save_img:
				# print(self.img_crypt)
				# cv.imwrite('/home/ayush/Desktop/Stuff/Random/PhotoCrypt/PhotoCrypt/lena_encrypted.jpeg', self.img_crypt, [int(cv.IMWRITE_JPEG_QUALITY), 100])
				cv.imwrite('/home/ayush/Desktop/Stuff/Random/PhotoCrypt/PhotoCrypt/lena_encrypted.png', self.img_crypt)

				# Testing lossless write
				
				read = (cv.imread('/home/ayush/Desktop/Stuff/Random/PhotoCrypt/PhotoCrypt/lena_encrypted.png'))


				# print(read - self.img_crypt)
				# unique, counts = np.unique((read - self.img_crypt), return_counts=True)
				# print(dict(zip(unique, counts)))


	def metric_vis(self): #visualise img difference, noisy LSB distribution
		cv.imshow('difference', self.img_crypt-self.img)
		cv.imshow('encoded', self.img_crypt)

		ori_dist = np.zeros_like(self.img)
		new_dist = np.zeros_like(self.img)

		for k in range(self.num_channels):
			for i in range(self.IMG_SIZE):
				for j in range(self.IMG_SIZE):
					last_two = conv_bin(self.img[i,j,k], 8)[6:]
					ori_dist[i,j,k] = int(conv_dec(last_two)/4 * 256)
	
		for k in range(self.num_channels):
			for i in range(self.IMG_SIZE):
				for j in range(self.IMG_SIZE):
					last_two = conv_bin(self.img_crypt[i,j,k], 8)[6:]
					new_dist[i,j,k] = int(conv_dec(last_two)/4 * 256)

		cv.imshow('original distribution', ori_dist)
		cv.imshow('new distribution', new_dist)
		cv.imshow('distribution diff', new_dist-ori_dist)

		cv.waitKey(0)
		cv.destroyAllWindows()



if __name__ == '__main__':
	msg = 'Hello this is a test image. I am trying to hide this message.'
	# msg = 'Lorem ipsum dolor sit amet. Id sunt possimus rem ratione consequatur  reprehenderit saepe aut saepe placeat non sapiente veritatis quo voluptatem eaque aut praesentium autem? Cum dolores sint est enim quaerat et consequatur recusandae qui temporibus suscipit. Et eveniet corporis est quia magni est veritatis omnis ad expedita excepturi et fugiat vitae At reiciendis quasi. Non ipsum Quis nam nostrum voluptate et magnam corrupti vel recusandae consequatur qui assumenda aperiam ut nihil assumenda! Aut sequi animi qui voluptas magni ut nemo laborum aut expedita consequatur et animi consectetur ut veritatis Quis. Sit dolores quis quo consequatur sint qui eius esse est excepturi dolorem. Deserunt impedit eos architecto officia et minima officiis id doloribus laudantium sit voluptatum eligendi et vitae sint ab rerum impedit. Id deserunt saepe et tenetur repudiandae est ratione doloremque aut enim quia id earum dolor. </p><p>Sit ipsam omnis est consequatur culpa et saepe nostrum est atque sapiente qui dolores quis ut repellat expedita? A voluptate aperiam et eveniet cupiditate sed fuga dicta aut excepturi voluptatem qui sint aperiam! Vel cupiditate consequatur et asperiores suscipit vel aliquid tempore qui veritatis sunt et voluptatum minus At necessitatibus quas est maxime vero. Sed amet unde id odit rerum ut quasi velit ut rerum aspernatur. Qui obcaecati molestiae sit repellat internos id eaque laborum et magnam molestiae. Qui praesentium nihil hic voluptate suscipit aut rerum mollitia est nostrum quasi ad expedita deleniti eum debitis repudiandae. 33 officia mollitia et perferendis officia et perspiciatis velit. Et minima esse non fugiat excepturi ab quisquam necessitatibus At consequatur tempora est dolor internos ut distinctio nulla. </p><p>Ea doloribus mollitia ut libero nobis ut reiciendis numquam non error perferendis eos ipsam sint. Sed recusandae doloribus qui provident soluta qui voluptas aliquid ut delectus blanditiis rem possimus excepturi et adipisci veritatis. Qui ullam totam ea nostrum rerum aut saepe quas eos excepturi odio. A voluptates error ex adipisci modi qui ullam ipsam et quod deserunt qui nihil consequuntur  Quis tempore? Ut culpa possimus et quasi nulla sed consequatur minus qui deserunt quibusdam vel animi quos et labore excepturi! Qui iste possimus ad illum tenetur sit nemo harum qui debitis laudantium ad quia rerum ex nemo debitis! Eos omnis quasi est harum nulla rem vitae mollitia non quasi provident. Sit repellat itaque sed culpa Quis nam reiciendis internos aut amet aliquid ab sunt debitis et enim reiciendis hic explicabo nihil! </p><p>Est corporis vitae et alias dolorum et nobis corrupti! Et itaque excepturi et adipisci Quis aut distinctio nisi sed ullam temporibus et tempore quasi. Ad voluptatem dolor et iure omnis aut ducimus nihil et aliquam nobis. Et recusandae quibusdam sit numquam eveniet 33 dignissimos omnis et voluptatem eius a velit rerum et unde nihil. Quo consectetur dolore a amet error cum perferendis perspiciatis est obcaecati magni ut dolores asperiores. Sed dolorem illum aut commodi quibusdam sit possimus cupiditate ut dicta fugit non laborum quod est nulla expedita. Est asperiores fugit ut velit eius  voluptatibus ipsum est doloribus voluptatem! Vel maiores totam et excepturi laudantium aut reiciendis possimus sit rerum quidem qui facere officia. Qui tempore beatae ad aliquam fugiat  corrupti autem eum placeat delectus? At exercitationem velit eum numquam perferendis eos tempore repudiandae qui omnis porro et omnis dicta vel dicta ipsum et iste ipsum. Sed dolorem voluptatibus rem atque voluptas eos necessitatibus unde et similique accusamus eum architecto ullam vel totam distinctio ea voluptas maiores. </p><p>Aut minima ducimus non provident perspiciatis est ratione quaerat sed architecto recusandae aut ipsa nesciunt et modi molestiae. Sed ipsum magnam ut minima officiis ea consequatur obcaecati eos commodi modi ut libero ipsa a porro quod eum consequuntur esse. 33 ratione iure est assumenda voluptas ab laboriosam dolorem quo modi ipsam qui iste odio aut optio nobis. Est corrupti ducimus et adipisci illum eum sunt sint ut galisum incidunt. Est molestiae temporibus aut quod fuga et odit ratione ut explicabo odio et assumenda voluptate eum doloremque laboriosam. Non placeat dolor sed harum corrupti qui accusantium temporibus vel rerum molestiae. Ad magni iste et delectus autem sed harum aliquam! Est libero ipsam et quas enim sit incidunt magni ea consequuntur corporis non aliquid adipisci. Est mollitia maxime est consequatur dolorem et autem velit et laboriosam dolor aut assumenda voluptatem. Qui reiciendis explicabo 33 laudantium sint et ipsa voluptatum. Aut harum quibusdam ut consectetur ducimus et praesentium animi ea nihil voluptas. Ut saepe suscipit et nesciunt fuga vel nihil quia ut nulla dolores hic consequatur consequatur. Qui itaque laborum non voluptates voluptas vel quam facere qui consequuntur accusantium non nihil optio vel rerum obcaecati. Sit nesciunt dolore qui assumenda libero non voluptatem iusto et nihil voluptatibus aut enim fuga sit ipsum expedita. </p><p>Aut incidunt  et asperiores excepturi ut consequatur porro in obcaecati architecto. Eos quisquam mollitia ut sapiente autem ad internos beatae ut corrupti quae in dolore labore. Aut autem consequatur quo omnis omnis ut laudantium nostrum sit nostrum labore et atque nihil qui galisum Quis ea consequatur consequatur. Id praesentium aperiam non voluptas iste eos consequatur magnam  deleniti reiciendis qui eaque nostrum vel doloremque officiis ut voluptatum dignissimos? Et voluptatem nobis aut adipisci beatae a adipisci asperiores cum perferendis sunt et rerum aliquid. Ut accusantium sequi rem harum eligendi ab nesciunt deserunt qui nihil harum eum maiores illum qui nesciunt repellendus. Ex soluta nemo non vero dolores qui enim enim vel laudantium impedit eum deleniti nihil eum omnis dignissimos. Et autem nihil est voluptate modi in quidem excepturi ea unde nihil ut sunt minima. Est magni minima quo sint aliquid in inventore velit ut molestias quidem aut quibusdam libero est expedita atque. Et expedita dolorum et ullam doloribus et consectetur dolorem quo necessitatibus dolorem? Eum consequatur explicabo 33 excepturi illum in exercitationem magni. '
	# msg = 'N'

	encrypt = True

	p = photo_encoder()
	p.read_image()
	
	if encrypt:
		msg = p.encryptor(msg)
	
	bin_msg = p.binarise_message(msg, encrypt)
	p.get_crypt_dict(bin_msg)
	p.encode_image()


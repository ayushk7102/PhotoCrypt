# PhotoCrypt
A cryptographic system to encrypt and encode text data within pixel values of a lossless PNG image.

### Metadata
Header metadata stores the following information: (offset, message_length). 

Offset denotes a random index of the flattened image array where the message encoding begins.
Message_length is represented in 2-bit pairs. 

Metadata is encoded at a specific location in the image, and must be decoded at the receiver's end prior to decrypting the hidden message.

### Encryption 
Messages are encrypted using AES cipher block chaining mode, to get a secure cipher text. The cipher text is converted to raw binary form, and at an offset in the image, the data is encoded within the least significant bits of the image pixels. 


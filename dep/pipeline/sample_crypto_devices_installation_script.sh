#SPDX-License-Identifier: BSD-3-Clause
#Copyright(c) 2023 Intel Corporation

#!/usr/bin/env bash
#set -o xtrace

NASM_VERSION=2.15.05
NASM_TAR_FILE=nasm-$NASM_VERSION.tar.gz
NASM_DIR=nasm-$NASM_VERSION
NASM_INSTALLATION_LINK=https://www.nasm.us/pub/nasm/releasebuilds/$NASM_VERSION/$NASM_TAR_FILE
IPSEC_AESNI_MB_BRANCH_TAG=v1.2
INSTALLATION_PATH=~

#Switching to installation directory path
echo "Switching to installation directory path: $INSTALLATION_PATH."
cd $INSTALLATION_PATH

if [ -d "$INSTALLATION_PATH/crypto_devices" ]
then
	#Removing previously created crypto device directory
	echo "Removing crypto directories at the $INSTALLATION_PATH path."
	rm -rf crypto_devices
fi

#Creating crypto device directory at installation path
echo "Creating installation directory at $INSTALLATION_PATH."
mkdir crypto_devices

#Switching to crypto device directory
echo "Switching to installation directory."I
cd crypto_devices
echo "Switched to installation directory."

#Installing NASM
echo "Installing NASM...."
wget $NASM_INSTALLATION_LINK
tar -xvf $NASM_TAR_FILE
cd $NASM_DIR
./configure
make
sudo make install
echo "NASM installed successfully."

#Installing IPSEC_AESNI_MB
#Switching back to installation directory
cd ../
echo "Installing IPSEC_AESNI_MB...."
git clone https://github.com/intel/intel-ipsec-mb.git
cd intel-ipsec-mb/
git checkout tags/$IPSEC_AESNI_MB_BRANCH_TAG
make
sudo make install
echo "IPSEC_AESNI_MB installed successfully."
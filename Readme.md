# Setup 

first make sure you have libvirt installed on your system. 

```bash
sudo apt install -y libvirt-dev python3-libvirt
```

then to verify that libvirt is installed correctly, run the following command:

```bash
pkg-config --modversion libvirt
```

output should be a no ( in our case it is 8.0.0)

Then make sure you have python3.11 installed on your system. 
and also poetry installed on your system. 

if you don't have poetry installed on your system, you can install it by checking the official documentation of poetry. 

then run the following command to install the dependencies:

```bash
poetry install
```

then run the following command to activate the virtual environment:

```bash

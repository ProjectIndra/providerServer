# Setup 

first make sure you have libvirt installed on your system. 

```bash
sudo apt install -y libvirt-dev python3-libvirt
```

also make sure you have given correct permissions to the user to access the libvirt.
```bash
sudo chown -R avinash:avinash /home/avinash/cloud_project/providerServer/images/
sudo chmod -R 775 /home/avinash/cloud_project/providerServer/images/
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

# build deb file from the builcommand.txt and put in the repo -> curl/sudo apt install mega -> 
# after installing the package the code will be put in the folder '/opt/mega' which will be created own it's own (mega folder) ->
# postinst.sh file will be executed where config file is created inside /etc/mega and all the required key/details are put ->
# demo.sh is executed which is used to install the base.qcow image ->
# Then venv is setup, systemd is reloaded and service is enabled ->
# Then mega.service is run where provider server is started and then tunnel/ngrok is created

# process:

# build the deb file from the buildCommand.txt and push the .deb file (mega_1.0.0_amd64.deb) to the fileshare.computekart.com using scp 

# curl command to install the mega package from fileshare.computekart.com - curl -L -o mega https://fileshare.computekart.com/mega_1.0.0_amd64.deb

# sudo apt remove --purge mega

# sudo dpkg -i mega
# sudo apt --fix-broken install -y  # This fixes missing dependencies automatically


# to check logs -
#journalctl -u mega.service -b

# curl -sL https://fileshare.computekart.com/install_mega.sh | sudo INSTALL_TOKEN=your_token bash
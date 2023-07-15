sudo apt install libpcap-dev libssl-dev libpcap0.8-dev
wget http://pkgs.fedoraproject.org/repo/pkgs/cowpatty/cowpatty-4.6.tgz/b90fd36ad987c99e7cc1d2a05a565cbd/cowpatty-4.6.tgz
tar zxfv cowpatty-4.6.tgz
cd cowpatty-4.6/
make -s
sudo cp cowpatty /usr/bin
sudo cp genpmk /usr/bin
cd ..
rm -rf cowpatty-4.6
rm cowpatty-4.6.tgz

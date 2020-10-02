
#include <iostream.h>
#include <windows.h>
#include <winreg.h>

#define MYKEY "Software\\GibbiSoft\\Serial"
#define SERIAL "3123-1111-1223"

bool checkData() 
{
	char sn[255];
	LONG size;
	// ....
	return (RegQueryValue(HKEY_CURRENT_USER,MYKEY,sn,&size) == ERROR_SUCCESS)
			&& strcmp(sn,SERIAL) == 0;		

}

bool storeData() 
{
	char sn[255];
	HKEY serial;
	RegCreateKey(HKEY_CURRENT_USER,
				 MYKEY,
				 &serial);
	cout << "Enter a valid serial number:";
	cin >> sn;
	RegSetValue(serial,"",REG_SZ,sn,strlen(sn));
	return false;
}

bool firstRun()
{
	HKEY serial;
	return (RegOpenKey(HKEY_CURRENT_USER,MYKEY,&serial) != ERROR_SUCCESS);
}

int main(int argc, char* argv[])
{
	if (firstRun())
		storeData();
	if (!checkData()) {
			cout << "Registration informations are not valid\n";
			return -1;
		}
    cout << "OK. Starting Gib 2.1\n";
	// ...
	return 0;
}

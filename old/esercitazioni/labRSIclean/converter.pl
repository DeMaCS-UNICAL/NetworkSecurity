#! /usr/bin/perl

#
#  Netkit .startup to interfaces converter
#
while (<>)

{
   if ( ($dev,$ip,$mask,$broadcast)  = /ifconfig (\w+?) (\d+?\.\d+?\.\d+?\.\d+?) netmask (\d+?\.\d+?\.\d+?\.\d+?) / ) {
	$device{$dev} = "auto $dev\niface $dev inet static\n\taddress $ip\n\tnetmask $mask\n"; }
   if ( ($dev) = /route add .* dev (\w+)/ ) {
	$device{$dev} .= "\tup $_\n"; }
}

foreach (keys %device)
{
    print "$device{$_}\n";	
}


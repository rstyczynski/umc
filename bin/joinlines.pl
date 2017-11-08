#!/usr/bin/perl

use Getopt::Long;
use Pod::Usage;
use strict;
use warnings;

my $man=0;			#man flag
my $help=0;			#help flag
my $verbose=0;     #verbose flaga
my $notbuffered=1;
my $endMark;     #stop word

#read cmd line options
my $optError=0;
GetOptions ('stop=s'   	=> \$endMark,      	# string
	    'notbuffered'  => \$notbuffered, #flag
            'verbose'	=> \$verbose,      	# flag
            'help|?'	=> \$help, 		    # flag
            'man'		=> \$man)           # flag
or $optError=1;

if($optError){
	print ("joinlines.pl: Error in command line arguments\n");
	pod2usage(2);
	exit;
}

pod2usage(1) if $help;
pod2usage(-exitstatus => 0, -verbose => 2) if $man;


if (not defined $endMark) {
	print ("joinlines.pl: Error in command line arguments\n");
	pod2usage(2);
	exit;
}

if ( $notbuffered ) {
   $|=1
}

while (<STDIN>) {
  my $line = $_;
  chomp $line;
  if ( $line =~ /$endMark/ ) {
    print "$line\n"
  } else {
    print "$line,";
  }
}

__END__

=head1 NAME

 joinlines.pl - join multiline records into one line.

=head1 SYNOPSIS

some_program 2>&1 | perl joinlines.pl -stop endWord
 where:
  -stop - keep newline character in line with stop word

=head1 DESCRIPTION

Joins lines together stopping on a line with stop word.

=head1 EXAMPLES

ifconfig
eth0      Link encap:Ethernet  HWaddr 00:1c:42:ec:f5:ce  
          inet addr:10.37.129.5  Bcast:10.37.129.255  Mask:255.255.255.0
          inet6 addr: fdb2:2c26:f4e4:1:21c:42ff:feec:f5ce/64 Scope:Global
          inet6 addr: fe80::21c:42ff:feec:f5ce/64 Scope:Link
          inet6 addr: fdb2:2c26:f4e4:1:7137:48fe:abc1:5631/64 Scope:Global
          UP BROADCAST RUNNING MULTICAST  MTU:1500  Metric:1
          RX packets:99990 errors:0 dropped:0 overruns:0 frame:0
          TX packets:87208 errors:0 dropped:0 overruns:0 carrier:0
          collisions:0 txqueuelen:1000 
          RX bytes:7327668 (7.3 MB)  TX bytes:10158541 (10.1 MB)

ifconfig eth0 | grep -i X 
          RX packets:100876 errors:0 dropped:0 overruns:0 frame:0
          TX packets:87767 errors:0 dropped:0 overruns:0 carrier:0
          collisions:0 txqueuelen:1000 
          RX bytes:7401861 (7.4 MB)  TX bytes:10235143 (10.2 MB)

ifconfig eth0 | grep -i X | perl joinlines.pl "RX bytes"
          RX packets:100903 errors:0 dropped:0 overruns:0 frame:0,          TX packets:87788 errors:0 dropped:0 overruns:0 carrier:0,          collisions:0 txqueuelen:1000 ,          RX bytes:7403979 (7.4 MB)  TX bytes:10238249 (10.2 MB)
          
ifconfig eth0 | grep -i X | perl joinlines.pl -stop "RX bytes" | sed -u 's/[a-z:]//g' | sed -u 's/  */,/g' | cut -d',' -f3-7,10-13,16-17,21,25
101115,0,0,0,0,87927,0,0,0,0,1000,7421707,10255719

=back

=head1 AUTHOR

Ryszard Styczynski
<ryszard.styczynski@oracle.com>
<http://snailsinnoblesoftware.blogspot.com>
November 2015, version 0.1

=cut


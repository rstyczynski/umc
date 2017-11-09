#!/usr/bin/perl


use Getopt::Long;
use Pod::Usage;
#use strict;
#use warnings;

my $man=0;                      #man flag
my $help=0;                     #help flag
my $verbose=0;     #verbose flaga
my $notbuffered=0;
my $dateTimeDelimiter=",";

#read cmd line options
my $optError=0;
GetOptions (
            'delimiter=s'  => \$dateTimeDelimiter, #string
            'notbuffered'  => \$notbuffered,       #flag
            'verbose'      => \$verbose,           # flag
            'help|?'       => \$help,              # flag
            'man'          => \$man)               # flag
or $optError=1;



$DEBUG=$verbose;

if ( $notbuffered ) {
  $| = 1;
}



while (<>) {
	($sec, $min, $hour, $day, $mon, $year) = localtime;
	if($DEBUG eq 1){
		print $min . ":" .$sec . " vs. " .$minPrint.":". $secPrint . "->";
	}
	if ( $sec >= ($secPrint + 2) || ($min != $minPrint) ){
		($secPrint, $minPrint, $hourPrint, $dayPrint, $monPrint, $yearPrint) = 
								($sec, $min, $hour, $day, $mon, $year);
	}
	#format: 2010-11-20,16:44:34,
	printf("%04d-%02d-%02d" . $dateTimeDelimiter . "%02d:%02d:%02d", 1900 + $yearPrint, $monPrint + 1, $dayPrint,
						$hourPrint, $minPrint, $secPrint);
	print ",$_";
}


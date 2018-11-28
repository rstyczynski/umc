#!/usr/bin/perl
#------------------------------------------------------------------------------#
# SCRIPT: perf_parse.pl
#
# DESCRIPTION:
#
# Script to parse the output of the BRM opcode profiling library. This provides
# simple summary information, but in most cases this should be sufficient to
# identify where there are performance issues.
#
# INFORMATION:
#
# BRM Performance tools ...
#
# REVISION:
#
# $Revision: 1.71 $
# $Author: pin $
# $Date: 2015/04/20 19:02:03 $
#------------------------------------------------------------------------------#
use File::Basename;
use Getopt::Std;
use locale;

#
# Hash of base opcodes ... 
#
%BASE_OPCODES = (
   "PCM_OP_CREATE_OBJ" => 1,
   "PCM_OP_DELETE_OBJ" => 1,
   "PCM_OP_READ_OBJ" => 1,
   "PCM_OP_READ_FLDS" => 1,
   "PCM_OP_WRITE_FLDS" => 1,
   "PCM_OP_DELETE_FLDS" => 1,
   "PCM_OP_SEARCH" => 1,
   "PCM_OP_INC_FLDS" => 1,
   "PCM_OP_LOGIN" => 1,
   "PCM_OP_LOGOFF" => 1,
   "PCM_OP_TEST_LOOPBACK" => 1,
   "PCM_OP_TRANS_OPEN" => 1,
   "PCM_OP_TRANS_ABORT" => 1,
   "PCM_OP_TRANS_COMMIT" => 1,
   "PCM_OP_PASS_THRU" => 1,
   "PCM_OP_GET_CM_STATS" => 1,
   "PCM_OP_STEP_SEARCH" => 1,
   "PCM_OP_STEP_NEXT" => 1,
   "PCM_OP_STEP_END" => 1,
   "PCM_OP_GET_DD" => 1,
   "PCM_OP_SET_DD" => 1,
   "PCM_OP_GLOBAL_SEARCH" => 1,
   "PCM_OP_GLOBAL_STEP_SEARCH" => 1,
   "PCM_OP_GLOBAL_STEP_NEXT" => 1,
   "PCM_OP_GLOBAL_STEP_END" => 1,
   "PCM_OP_SET_DM_CREDENTIALS" => 1,
   "PCM_OP_EXEC_SPROC" => 1,
   "PCM_OP_LOCK_OBJ" => 1,
   "PCM_OP_GET_POID_IDS" => 1,
   "PCM_OP_BULK_WRITE_FLDS" => 1,
   "PCM_OP_BULK_DELETE_OBJ" => 1,
   "PCM_OP_BULK_CREATE_OBJ" => 1,
);

use constant {
   #
   # Aggregation data array indexes ...
   #
   AGG_NAME_IDX        => 0,
   AGG_SOURCE_IDX      => 1,
   AGG_PROGRAM_IDX     => 2,
   AGG_OPFLAGS_IDX     => 3,
   AGG_DURATION_IDX    => 4,
   AGG_U_CPU_IDX       => 5,
   AGG_S_CPU_IDX       => 6,
   AGG_COUNT_IDX       => 7,
   AGG_ERRORS_IDX      => 8,
   AGG_RECORDS_IDX     => 9,
   AGG_MAX_IDX         => 10,
   AGG_MIN_IDX         => 11,
   AGG_BUCKET_ID_IDX   => 12,
   AGG_BUCKET_FROM_IDX => 13,
   AGG_BUCKET_TO_IDX   => 14,
   AGG_CACHE_COUNT_IDX => 15,
   AGG_CACHE_TIME_IDX  => 16,
   AGG_SUB_OPCODES_IDX => 17,
   AGG_OBJ_TYPE_IDX    => 18,
   #
   # Trace file versions
   #
   TRACE_FILE_VERSION_1 => 1,
   TRACE_FILE_VERSION_2 => 2,
   #
   # Other miscellaneous constants ...
   #
   CM_TXN_OPNAME       => "*TXN*",
   BUCKET_FMT_LENGTH   => 45,
   DEPTH_UNLIMITED     => 999999,
};

#------------------------------------------------------------------------------#
# Function     : oppath_on_filter_path
#
# Description  : Checks whether a given oppath is on our filter path. This will
#                return 0 if there is no match (i.e. we don't want to count the
#                opcode at all), 1 if on the path and after the filter (so we
#                want to count the time), and -1 if it's on the path but we're
#                not yet at our full filter length.
#
# Input        : aref       Opcode path stack array reference
#                fp_aref    Filter path array ref (or scalar if only one) ...
#                
# Output       : None
#
# Return       : 0 if no match, 1 if on path (count), -1 if on path (no count)
#------------------------------------------------------------------------------#
sub oppath_on_filter_path {
   my ($aref, $fp_aref) = @_;

   $fp_aref = [ $fp_aref ] if (ref($fp_aref) eq "SCALAR");
   my $i = 0;
   for ($i = 0; $i <= $#{$aref}; $i++) {
      if ($i > $#{$fp_aref}) {
         # There are no more filter elements - so we match
         return 1;
      } elsif ($fp_aref->[$i] ne $aref->[$i]) {
         # Filter does not match  ...
         return 0;
      }
   }
   # We matched all elments - but are we still "inside" the filter path or not?
   my $rv = $i <= $#{$fp_aref} ? -1 : 1;
   return $rv;
}

#------------------------------------------------------------------------------#
# Function     : init_opcode_data
#
# Description  : Create a new opcode record - done as we descend the opcode
#                stack and encounter new opcodes. All key values are populated
#                and all counters initialized to zero.
#
# Input        : opname     Opcode name
#                op_source  Source code data
#                program    Program name
#                opflags    Opcode flags
#                obj_type   Object type
#                bucket_id  Bucket ID
#                
# Output       : None
#
# Return       : array reference
#------------------------------------------------------------------------------#
sub init_opcode_data {
   my ($opname, $op_source, $program, $opflags, $obj_type,
       $bucket_id) = @_;

   my $aref = [];
   $aref->[AGG_NAME_IDX] = $opname;
   $aref->[AGG_SOURCE_IDX] = $op_source;
   $aref->[AGG_PROGRAM_IDX] = $program;
   $aref->[AGG_OBJ_TYPE_IDX] = $obj_type;
   $aref->[AGG_OPFLAGS_IDX] = $opflags;
   $aref->[AGG_DURATION_IDX] = 0;
   $aref->[AGG_U_CPU_IDX] = 0;
   $aref->[AGG_S_CPU_IDX] = 0;
   $aref->[AGG_COUNT_IDX] = 0;
   $aref->[AGG_ERRORS_IDX] = 0;
   $aref->[AGG_RECORDS_IDX] = 0;
   $aref->[AGG_MIN_IDX] = 0;
   $aref->[AGG_MAX_IDX] = 0;
   $aref->[AGG_CACHE_COUNT_IDX] = 0;
   $aref->[AGG_CACHE_TIME_IDX] = 0;
   $aref->[AGG_BUCKET_ID_IDX] = $bucket_id;
   $aref->[AGG_SUB_OPCODES_IDX] = {};

   return $aref;
}

#------------------------------------------------------------------------------#
# Function     : update_opcode_data
#
# Description  : Update an opcode record - done when we encounter an opcode
#                end record. The array references is provided, so we just need
#                to increment all the totals appropriately.
#
#                NOTE: We also set the bucket range times here as, for some
#                      lapse of reason, the bucket ID is on the start record
#                      but the time ranges are not :-).
#
# Input        : aref       Opcode data array reference
#                call_cnt   Number of opcode calls
#                duration   Total duration of the calls
#                err_cnt    Number of errors
#                rec_cnt    Number of records retrieved (search or rflds/robj)
#                cache_cnt  Number of operations returned from cache
#                cache_t    Time for operations returned from cache
#                min_t      Minimum opcode execution time (excluding failures)
#                max_t      Maximum opcode time
#                u_cpu      User CPU time
#                s_cpu      System CPU time
#                st_rng_t   Update bucket start range (if not done already)
#                end_rng_t  Update bucket end range (if not done already)
#                
# Output       : None
#
# Return       : None
#------------------------------------------------------------------------------#
sub update_opcode_data {
   my ($aref, $call_cnt, $duration, $err_cnt, $rec_cnt, $cache_cnt, $cache_t,
       $min_t, $max_t, $u_cpu, $s_cpu, $st_rng_t, $end_rng_t) = @_;

   $aref->[AGG_DURATION_IDX] += $duration;
   $aref->[AGG_U_CPU_IDX] += $u_cpu;
   $aref->[AGG_S_CPU_IDX] += $s_cpu;
   $aref->[AGG_COUNT_IDX] += $call_cnt;
   $aref->[AGG_ERRORS_IDX] += $err_cnt;
   $aref->[AGG_RECORDS_IDX] += $rec_cnt;
   $aref->[AGG_CACHE_COUNT_IDX] += $cache_cnt;
   $aref->[AGG_CACHE_TIME_IDX] += $cache_t;
   if ($call_cnt > 0) {
      if ($aref->[AGG_MIN_IDX] == 0 || $aref->[AGG_MIN_IDX] > $min_t) {
         $aref->[AGG_MIN_IDX] = $min_t;
      }
      if ($aref->[AGG_MAX_IDX] < $max_t) {
         $aref->[AGG_MAX_IDX] = $max_t;
      }
   }
   $aref->[AGG_BUCKET_FROM_IDX] = $st_rng_t;
   $aref->[AGG_BUCKET_TO_IDX] = $end_rng_t;
}

#------------------------------------------------------------------------------#
# Function     : aggregate_sort_func
#
# Description  : Perl sort method for sorting simple or "full-path" results.
#                'Simple' data is sorted by time (descending) whilst full-path
#                is printed in alphabetical order ...
#
# Input        : a    Sort key A
#                b    Sort key B
#
# Output       : None
#
# Return       : <0, 0, >0
#------------------------------------------------------------------------------#
sub aggregate_sort_func {
   if ($printing_full_path) {
      return $a cmp $b;
   } else {
      my $rv = $G_SIMPLE{$b}->[AGG_DURATION_IDX] <=>
               $G_SIMPLE{$a}->[AGG_DURATION_IDX];
      return $rv if ($rv);
      return $a cmp $b;
   }
}

#------------------------------------------------------------------------------#
# Function     : calc_max_oplen
#
# Description  : Calculate the maximum opcode with we need for the report. This
#                will either process the full stack or simple results based on
#                the '$printing_full_path' global.
#
#                This will process all opcodes in the hash and determine the
#                lengths for display - as necessary, recursion will be used to
#                calculate full "path" lengths.
#
# Input        : href       Hash ref of opcode entries
#
# Output       : None
#
# Return       : length of display string
#------------------------------------------------------------------------------#
sub calc_max_oplen {
   my ($href) = @_;
   return __calc_max_oplen ($href, 0);
}

sub __calc_max_oplen {
   my ($href, $depth) = @_;

   my $oplen = 0;
   my $len = 0;

   foreach my $aref (values %{$href}) {
      if ($p_dot_style) {
         #
         # If 'F' type filtering, the top-level filter opcodes are not
         # displayed.
         #
         if ($printing_full_path) {
            if ($p_filter_type eq "F" && $depth < $p_elapsed_level - 1) {
               $len = __calc_max_oplen ($aref->[AGG_SUB_OPCODES_IDX], $depth+1);
            } else {
               #
               # Adjust indentation for 'F' type filtering ...
               #
               my $indent = ($p_filter_type eq "F") ?
                               $depth-$p_elapsed_level+1 :
                               $depth;

               my $this_len = length($aref->[AGG_NAME_IDX]);
               if ($aref->[AGG_BUCKET_ID_IDX] > 0) {
                  $this_len += (BUCKET_FMT_LENGTH + 1);
               }
               #
               # Use recursion to get the sum of lower levels to add to this ...
               #
               $len = $this_len +
                      __calc_max_oplen ($aref->[AGG_SUB_OPCODES_IDX],
                                        $depth+1) +
                      ($indent > 0 ? 1 : 0);
            }
         } else { # Simple path
            if ($aref->[AGG_BUCKET_ID_IDX] > 0) {
               $len = length($aref->[AGG_NAME_IDX]) + BUCKET_FMT_LENGTH;
            } else {
               $len = length($aref->[AGG_NAME_IDX]);
            }
         }
         $oplen = $len if ($len > $oplen);
      } else { # Normal style
         if ($printing_full_path) {
            if ($p_filter_type eq "F" && $depth < $p_elapsed_level-1) {
               #
               # If 'F' type filtering, the top-level filter opcodes are not
               # displayed.
               #
               $len = 0; # won't be printed
            } else {
               #
               # Adjust indentation for 'F' type filtering ...
               #
               my $indent = ($p_filter_type eq "F") ?
                               $depth-$p_elapsed_level+1 :
                               $depth;
               if ($aref->[AGG_BUCKET_ID_IDX] > 0) {
                  $len = ($p_indent_size * $indent) + BUCKET_FMT_LENGTH;
               } else {
                  $len = ($p_indent_size * $indent) +
                         length($aref->[AGG_NAME_IDX]);
               }
           }
         } else { # simple path ...
            if ($aref->[AGG_BUCKET_ID_IDX] > 0) {
               $len = length($aref->[AGG_NAME_IDX]) + BUCKET_FMT_LENGTH;
            } else {
               $len = length($aref->[AGG_NAME_IDX]);
            }
         }
         $oplen = $len if ($len > $oplen);
         #
         # Recurse through the tree ...
         #
         $len = __calc_max_oplen ($aref->[AGG_SUB_OPCODES_IDX], $depth+1);
         $oplen = $len if ($len > $oplen);
      }
   }
   return $oplen;
}

#------------------------------------------------------------------------------#
# Function     : print_reports
#
# Description  : Print out the aggregate totals that we have maintained during
#                our parse of the file.
#
# Input        : elapsed         Elapsed time from the timing file.
#                opcode_elapsed  Time spent executing opcodes.
#                baseop_elapsed  Time spent executing base opcodes.
#                nfiles          Number of files aggregated to get this data
#
# Output       : None
#
# Return       : None
#------------------------------------------------------------------------------#
sub print_reports {
   my ($elapsed, $opcode_elapsed, $baseop_elapsed, $nfiles) = @_;
   my $opn;
   my $duration;
   my ($pct_tot, $pct_ela);
   my $op_ela = $opcode_elapsed / $nfiles;
   my $ela = $elapsed / $nfiles;

   #
   # Print main opcode report(s) ...
   #
   if ($p_full_path) {
      $printing_full_path = 1;
      $_max_len_composite = calc_max_oplen (\%G_FULL_PATH);
      print_main_report ($elapsed, $opcode_elapsed, $baseop_elapsed,
                         $nfiles);
   }

   if (!$p_no_single) {
      $printing_full_path = 0;
      $_max_len_single = calc_max_oplen (\%G_SIMPLE);
      print_main_report ($elapsed, $opcode_elapsed, $baseop_elapsed, $nfiles);
   }

   #
   # Print summary totals ...
   #
   printf "\n";
   printf "Totals\n";
   printf "======\n\n";
   printf "Total trace files   : %10d\n", $nfiles if ($nfiles > 1);
   printf "Total opcodes used  : %10d\n", scalar(keys %opcodes_used);
   printf "Total opcode calls  : %10d\n", $_op_tot_count;
   printf "   Average / cm     : %10d\n",
      int($_op_tot_count / $nfiles) if ($nfiles > 1);
   $tmp = 11 + $p_dp;
   printf "Opcode elapsed      : %${tmp}.${p_dp}f\n", $opcode_elapsed;
   printf "   Average / cm     : %${tmp}.${p_dp}f\n",
      $opcode_elapsed / $nfiles if ($nfiles > 1);
   printf "Base-Op elapsed     : %${tmp}.${p_dp}f (%.2f%%)\n",
      $baseop_elapsed, 100 * $baseop_elapsed / ($opcode_elapsed || 1);
   printf "Total Base-Op calls : %10d (%.2f%%)\n",
      $_opbase_tot_count, 100 * $_opbase_tot_count / ($_op_tot_count || 1);
   printf "Total opcode errors : %10d (%.2f%%)\n",
      $_op_tot_errors, 100 * $_op_tot_errors / ($_op_tot_count || 1);
}

#------------------------------------------------------------------------------#
# Function     : print_main_report
#
# Description  : Print out the main report details (either for the 'full-path'
#                or simple opcode report).
#
# Input        : elapsed         Elapsed time from the timing file.
#                opcode_elapsed  Time spent executing opcodes.
#                baseop_elapsed  Time spent executing base opcodes.
#                nfiles          Number of files aggregated to get this data
#
# Output       : None
#
# Return       : None
#------------------------------------------------------------------------------#
sub print_main_report {
   my ($elapsed, $opcode_elapsed, $baseop_elapsed, $nfiles) = @_;
   my $opn;
   my $duration;
   my ($pct_tot, $pct_ela);
   my $op_ela = $opcode_elapsed / $nfiles;
   my $ela = $elapsed / $nfiles;

   printf "\n";
   if ($printing_full_path) {
      printf "Full-path opcode call summary\n";
      printf "=============================\n";
   } else {
      printf "Single opcode call summary\n";
      printf "==========================\n";
   }

   #
   # Determine report-specific lengths ...
   #
   if ($printing_full_path) {
      if ($_max_len_composite > $col_attributes{o}{len}) {
         $col_attributes{o}{len} = $_max_len_composite;
      }
   } else {
      if ($_max_len_single > $col_attributes{o}{len}) {
         $col_attributes{o}{len} = $_max_len_single;
      }
   }
   if ($_max_len_prog > $col_attributes{P}{len}) {
      $col_attributes{P}{len} = $_max_len_prog;
   }
   if ($_max_len_src > $col_attributes{s}{len}) {
      $col_attributes{s}{len} = $_max_len_src;
   }
   if ($_max_len_obj_type > $col_attributes{O}{len}) {
      $col_attributes{O}{len} = $_max_len_obj_type;
   }

   #
   # Print headers ...
   #
   print_header ($p_attributes, undef);
   print_underline ($p_attributes);
   print_header ($p_attributes, $xlf) if ($p_excel);

   if ($printing_full_path) { 
      $xl_recid = 0;
      print_report_level (\%G_FULL_PATH, 0, $elapsed, $opcode_elapsed, "");
   } else {
      $xl_recid = 0;
      print_report_level (\%G_SIMPLE, 0, $elapsed, $opcode_elapsed, "");
   }
}

#------------------------------------------------------------------------------#
# Function     : print_report_level
#
# Description  : Print out a level of the report (either for the 'full-path'
#                or simple opcode report). This will recursively call itself
#                in the case of full-path to print all the details related to
#                lower-level opcode calls.
#
# Input        : href            Hash reference containing opcodes
#                depth           Depth in report (0, 1, 2 ...)
#                elapsed         Elapsed time from the timing file.
#                opcode_elapsed  Time spent executing opcodes.
#                dot_opstr       Opcode path as A.B.C
#
# Output       : None
#
# Return       : None
#------------------------------------------------------------------------------#
sub print_report_level {
   my ($href, $depth, $elapsed, $opcode_elapsed, $base_opstr) = @_;
   my $duration;
   my ($pct_tot, $pct_ela);

   my $indent = ($p_filter_type eq "F") ?
                   $depth - $p_elapsed_level + 1 :
                   $depth;

   foreach my $aggr_key (sort aggregate_sort_func keys %{$href}) {
      my $aref = $href->{$aggr_key};

      #
      # Get a few useful values ...
      #
      $opname = $aref->[AGG_NAME_IDX];
      $count = $aref->[AGG_COUNT_IDX];
      $errors = $aref->[AGG_ERRORS_IDX];
      $duration = $aref->[AGG_DURATION_IDX];
      $bucket_id = $aref->[AGG_BUCKET_ID_IDX];
      $u_cpu = $aref->[AGG_U_CPU_IDX];
      $s_cpu = $aref->[AGG_S_CPU_IDX];
      $opflags = $aref->[AGG_OPFLAGS_IDX];
      $program = $aref->[AGG_PROGRAM_IDX];
      $obj_type = $aref->[AGG_OBJ_TYPE_IDX];
      $source = $aref->[AGG_SOURCE_IDX];
      $records = $aref->[AGG_RECORDS_IDX];
      $min_t = $aref->[AGG_MIN_IDX];
      $max_t = $aref->[AGG_MAX_IDX];

      #
      # If we're filtering with the 'F' option and the count is zero, we
      # don't want to display these 'placeholder' paths...
      #
      if ($p_filter_type ne "F" || $count >= 0) {
         #
         # Calculate approximate percentage ... 
         #
         if (!$opcode_elapsed || $opcode_elapsed == $duration) {
            $pct_tot = "100.00"
         } else {
            $pct_tot = sprintf ("%4.2f", (100.0 * $duration) / $opcode_elapsed);
         }

         #
         # Determine opcode name string ...
         #
         if ($printing_full_path) {
            $main_opstr = ($p_indent_str x $indent) . $opname;
         } else {
            $main_opstr = $opname;
         }
         $dot_opstr = $base_opstr ? ($base_opstr . "." . $opname) : $opname;

         #
         # Determine bucket string ...
         #
         if ($bucket_id) {
            $xlbstr =  sprintf "_%02d_%010.6f_%010.6f", $bucket_id,
                          $aref->[AGG_BUCKET_FROM_IDX],
                          $aref->[AGG_BUCKET_TO_IDX];

            if ($p_dot_style && $printing_full_path) {
               $bstr = ".";
            } elsif ($printing_full_path) {
               $bstr = $p_indent_str;
            } else {
               # Single opcode ...
               $bstr = " | ";
            }

            #
            # Get count of all calls so we can print proportion in each
            # bucket.
            #
            my $new_aggr_key = $aggr_key;
            substr($new_aggr_key, -3) = "000";
            my $new_aref = $href->{$new_aggr_key};

            my $bucket_pct = 0.0;
            if ($new_aref->[AGG_COUNT_IDX] > 0) {
               $bucket_pct = ($count * 100.0) / $new_aref->[AGG_COUNT_IDX];
            }

            #
            # Determine bucket string ...
            #
            if ($p_dot_style) {
               $bstr .= sprintf "BUCKET[%02d][%010.6f-%010.6f][%.1f%%]",
                           $bucket_id,
                           $aref->[AGG_BUCKET_FROM_IDX],
                           $aref->[AGG_BUCKET_TO_IDX],
                           $bucket_pct;
            } else {
               $from = sprintf "%10.6f", $aref->[AGG_BUCKET_FROM_IDX];
               $to = ($aref->[AGG_BUCKET_TO_IDX] > 0.0)
                        ? (sprintf "%10.6f", $aref->[AGG_BUCKET_TO_IDX])
                        : ("  infinity");
               $bstr .= sprintf "BUCKET[%02d] $from - $to %5.1f%%",
                           $bucket_id, $bucket_pct;
            }
         } else {
            $bstr = "";
            $xlbstr = "";
         }

         #
         # Run through the list of attributes that we need to print in the
         # report and format each one and add to the report output. Excel files
         # always have the type (FP, SI) and record ID in the report as the
         # first two columns.
         #
         if ($p_excel) {
            printf $xlf "%s,%d", $printing_full_path ? "FP" : "SI", $xl_recid++;
         }
         my $i = 0;
         foreach my $opt (split(//, $p_attributes)) {
            my $len = 0;
            my $data;

            if ($opt eq "o") {         # Opcode name
               if ($p_dot_style) {
                  $data = $dot_opstr . $bstr;
               } else {
                  if ($printing_full_path && $bstr) { # Full-path bucket
                     $data = ($p_indent_str x $indent) . $bstr;
                  } else {
                     $data = $main_opstr . $bstr;
                  }
               }
               $len = $col_attributes{$opt}{len};
            } elsif ($opt eq "f") {    # Opcode flags
               $data = $opflags;
            } elsif ($opt eq "O") {    # Object type
               $len = $col_attributes{$opt}{len};
               $data = $obj_type;
            } elsif ($opt eq "P") {    # Program name
               $len = $col_attributes{$opt}{len};
               $data = $program;
            } elsif ($opt eq "t") {    # Total time
               $data = $duration;
            } elsif ($opt eq "p") {    # Percentage of total time
               $data = $pct_tot;
            } elsif ($opt eq "c") {    # Call count
               $data = $count;
            } elsif ($opt eq "e") {    # Error count
               $data = $errors;
            } elsif ($opt eq "a") {    # Average call time
               $data = $count ? $duration / $count : $duration;
            } elsif ($opt eq "m") {    # Minimum call time
               $data = $min_t;
            } elsif ($opt eq "x") {    # Maximum call time
               $data = $max_t;
            } elsif ($opt eq "r") {    # Number of records returned
               $data = $records;
            } elsif ($opt eq "s") {    # Source code reference
               $len = $col_attributes{$opt}{len};
               $data = $source;
               $data =~ s/;/\[/;
               $data =~ s/;/\]/;
               $data = "<unknown>" if (!$data);
            } elsif ($opt eq "U") {   # User CPU time
               $data = $u_cpu;
            } elsif ($opt eq "S") {   # System CPU time
               $data = $s_cpu;
            }

            #
            # Print data into report using appropriate format ...
            #
            printf "  " if ($i > 0); # column separator
            if ($len) {
               printf $col_attributes{$opt}{dfmt}, $len, $len, $data;
            } else {
               printf $col_attributes{$opt}{dfmt}, $data;
            }

            #
            # Print data into Excel file with appropriate format ...
            #
            if ($p_excel) {
               if ($opt eq "o") {
                  $data = $dot_opstr . $xlbstr;
               }
               $len = $col_attributes{$opt}{len};
               printf $xlf ",";
               printf $xlf $col_attributes{$opt}{xfmt}, $data;
            }
            $i++;
         }
         printf "\n";
         printf $xlf "\n" if ($p_excel);
      }

      #
      # Recurse to lower levels ...
      #
      my $sub_ref = $aref->[AGG_SUB_OPCODES_IDX];
      if ($sub_ref) {
         print_report_level ($sub_ref, $depth+1, $elapsed, $opcode_elapsed,
                             $dot_opstr);
      }
   }
}




#------------------------------------------------------------------------------#
# Function     : time_string
#
# Description  : Get the time string related to the 10343355.345434 time format
#                entry (e.g. convert the 10343355 - which is the number of
#                seconds since 1st Jan 1970 - into a YYYYMMDD HH:MI:SS string
#                for display purposes.
#
#                If verbose parameter is passed, output is in 'localtime'
#                default format that of strftime).
#
# Input        : tstr     Time string  (seconds since 1970)
#                verbose  Use verbose time format
#
# Output       : None
#
# Return       : Time string
#------------------------------------------------------------------------------#
sub time_string {
   my ($tstr, $verbose) = @_;
   my $time = "";

   if ($tstr =~ /(.*)\.(.*)/) {
      if ($verbose) {
         $time = localtime($1);
      } else {
         my ($ss, $mi, $hh, $dd, $mm, $yyyy, $wday,
             $yday, $isdst) = localtime($1);
         $yyyy += 1900;
         # Take care that we never have more than 6 digit-precision ...
         $time = sprintf("%04d/%02d/%02d %02d:%02d:%02d.%06d",
                         $yyyy, $mm+1, $dd, $hh, $mi, $ss, ($2 / 1000));
      }
   }
   return $time;
}

#------------------------------------------------------------------------------#
# Function     : time_string
#
# Description  : Get the time string related to the 10343355.345434 time format
#                entry (e.g. convert the 10343355 - which is the number of
#                seconds since 1st Jan 1970 - into a YYYYMMDD HH:MI:SS string
#                for display purposes.
#
#                If verbose parameter is passed, output is in 'localtime'
#                default format that of strftime).
#
# Input        : tstr     Time string  (seconds since 1970)
#                verbose  Use verbose time format
#
# Output       : None
#
# Return       : Time string
#------------------------------------------------------------------------------#
sub time_string {
   my ($tstr, $verbose) = @_;
   my $time = "";

   if ($tstr =~ /(.*)\.(.*)/) {
      if ($verbose) {
         $time = localtime($1);
      } else {
         my ($ss, $mi, $hh, $dd, $mm, $yyyy, $wday,
             $yday, $isdst) = localtime($1);
         $yyyy += 1900;
         # Take care that we never have more than 6 digit-precision ...
         $time = sprintf("%04d/%02d/%02d %02d:%02d:%02d.%06d",
                         $yyyy, $mm+1, $dd, $hh, $mi, $ss, ($2 / 1000));
      }
   }
   return $time;
}

#------------------------------------------------------------------------------#
# Function     : process_data_row
#
# Description  : Process a single row of the file and calculate the opcode
#                durations etc.
#
# Input        : fno          The current file number ...
#                rec_id       Record number in this file.
#                opstatus     (S)tart or (F)inish flag.
#                oplevel      Nesting level of opcode call
#                opid         Internal sequence num assigned by tracing library.
#                opcode       Opcode number
#                opflags      Flags used when calling opcode
#                opname       Name of opcode (PCM_OP_BILL_MAKE_BILL etc.)
#                optime       Timestamp when operation occurred.
#                fname        Filename which called opcode.
#                line_no      Line number in calling code.
#                pid          Process ID of CM executing this opcode.
#                tid          Thread ID of executing code.
#                rcnt         Record count (finish record) for search opcodes.
#                call_cnt     Call count (principally for aggregations).
#                min_t        Minimum opcode time (only for aggregations).
#                max_t        Maximum opcode time (only for aggregations).
#                bucket_id    Sub-range bucket ID (if it's set, the min and max
#                             values indicate the range)
#                st_rng_t     Start range of bucket
#                end_rng_t    End range of bucket
#                cache_calls  Number of calls executed by CM TXN cache
#                cache_t      Elapsed time of calls executed by CM TXN cache
#                err_cnt      Error count
#                u_cpu        User CPU time
#                s_cpu        System CPU time
#                prg_name     Program name
#                obj_type     Object type
#
# Output       : None
#
# Return       : None
#------------------------------------------------------------------------------#
sub process_data_row {
   my ($fno, $rec_id, $opstatus, $oplevel, $opid, $opcode, $opflags, $opname,
       $optime, $fname, $line_no, $pid, $tid, $rcnt, $call_cnt, $min_t, $max_t,
       $bucket_id, $st_rng_t, $end_rng_t, $cache_calls, $cache_t, $err_cnt,
       $u_cpu, $s_cpu, $prg_name, $obj_type) = @_;
   my $tstamp = "";
   my ($opduration, $start_time);

   #---------------------------------------------------------------------------#
   # INITIALISATION:
   #
   # o Prepare opcode name
   # o Determine whether source code, flags, and so on are required.
   # o Determine the opcode aggregation 'key'
   #---------------------------------------------------------------------------#
   return if ($bucket_id && !$p_buckets);

   $opname = opcode_name (\%p_opmap, $opcode, $opname);
   my $filt_val = 0;
   $optime = "0.0" if (!$optime);

   if ($p_show_src && $fname && length($line_no) > 0) {
      $op_source = "$fname;$line_no;";
      my $l = length($op_source);
      $_max_len_src = $l if ($l > $_max_len_src);
   } else {
      $op_source = "";
   }

   if ($p_show_prog) {
      my $l = length($prg_name);
      $_max_len_prog = $l if ($l > $_max_len_prog);
   } else {
      $prg_name = "";
   }

   if ($p_show_obj_type) {
      my $l = length($obj_type);
      $_max_len_obj_type = $l if ($l > $_max_len_obj_type);
   } else {
      $obj_type = "";
   }

   $opflags = 0 if (!$p_show_opflags);

   $aggr_key = "$prg_name+$opname+$opflags+$op_source+$obj_type+" .
               sprintf("%03d", $bucket_id); # For correct sorting

   #---------------------------------------------------------------------------#
   # FILTERING ...
   #
   # o Filter out opcode bucket information if it's not required for the report.
   #---------------------------------------------------------------------------#
   if ($opname ne "VRT_OP_ELAPSED") {
      push (@G_FILTER_STACK, $opname) if ($opstatus eq "S");
      #
      # Check for user-specified filters ...
      #
      if ($#p_filter >= 0) {
         $filt_val = oppath_on_filter_path (\@G_FILTER_STACK, \@p_filter);
         #
         # If we're filtering, a return value of zero means that
         # we're not on the filter path... so nothing to do, just
         # return.
         #
         if ($filt_val == 0) {
            pop (@G_FILTER_STACK) if ($opstatus eq "F");
            return;
         }
      }

      #
      # Check for login filter ...
      #
      if ($p_filter_login) {
         foreach my $op_aref ($p_remove_pcm_op ?
                                 @LOGIN_FILTER :
                                 @login_filter)
         {
            #
            # If our path is on the same path as the login, we
            # don't have anything to do - so just return.
            #
            if (oppath_on_filter_path (\@G_FILTER_STACK, $op_aref) != 0) {
               pop (@G_FILTER_STACK) if ($opstatus eq "F");
               return;
            }
         }
      }
      pop (@G_FILTER_STACK) if ($opstatus eq "F");
   }

   #
   # Keep a count of distinct opcodes we're using (must be calculated AFTER
   # filtering) ...
   #
   if ($opname !~ /^VRT_OP/ && $p_fp_depth >= $oplevel) {
      $opcodes_used{$opname} = 1;
   }

   #---------------------------------------------------------------------------#
   # MAIN_PROCESSING:
   #
   # o Start records:
   #    - Print verbose and call-stack details (if required)
   #    - Initialise opcode tree entries
   #    - Stack opcode entry times to facilitate duration calculation
   #
   # o Finish records:
   #    - Pop opcode start information from stack and determine elapsed time
   #    - Update opcode tree entries ...
   #    - Print verbose and call-stack details (if required)
   #---------------------------------------------------------------------------#
   if ($opstatus eq "F") {
      #
      # Finish record:
      #
      # Find the relevant start record based on the level and print the
      # time (we just pop the record off the stack - which must
      # be our start record unless the source file is corrupt!).
      #
      # If this is a virtual opcode recording the elapsed time, just
      # calculate the elapsed time and don't bother with the other
      # logic.
      #
      if ($opname eq "VRT_OP_ELAPSED") {
         $elapsed_t += ($optime - $elapsed_start_t);
         $start_time = "0";
      } else {
         $start_time = pop (@_optime);
      } 
      if ($start_time eq "") {
         die ("No start record for finish record at line $rec_id\n");
      }

      #
      # Calculate opcode duration and update global totals ...
      #
      $opduration = sprintf("%.${p_dp}f", $optime - $start_time);
      if (!$bucket_id && $p_fp_depth >= $oplevel && $opname !~ /VRT_OP/) {
         $_op_tot_count += $call_cnt;
         $_op_tot_errors += $err_cnt;
      }

      #
      # If this is part of the filter expression (but not the part that we're
      # counting, reset all totals to zero).
      #
      if ($filt_val < 0) {
         $opduration = 0.0;
         $min_t = 0.0;
         $max_t = 0.0;
         $rcnt = 0;
         $call_cnt = -1; # Used to indicate filtered - impossible value
         $err_cnt = 0;
         $cache_calls = 0;
         $cache_t = 0.0;
      }

      #
      # OK, an opcode has finished at level 'X'. Therefore, we can update the
      # total at level 'X-1' (i.e. the sum of sub-opcodes). We also need to
      # determine the difference between the time taken to execute this
      # opcode (i.e. $opduration) and the opcodes which it called
      # ($p_level_totals[$oplevel]). If there's a difference (which there
      # is nearly always going to be) then we add a 'fake' "VRT_..." opcode
      # to our aggregates to track this ...
      #
      $non_op_name = "";
      $non_op_time = "";
      $non_op_aggr_key = "";
      if ($p_rpt_non_op) {
         #
         # We add some logic to keep the report tidy for bottom-level "base"
         # opcodes (i.e. those which call no others). If we find an opcode
         # with no sub-level times then we optionally exclude base-opcodes
         # from having a 'virtual' entry ...
         #
         if (($p_level_totals[$oplevel] <= 0.0) ||
             (($opduration - $p_level_totals[$oplevel]) <= 0.0) ||
             ($p_rpt_non_op == 1 && opcode_is_base($opname)))
         {
            $non_op_time = "";
         } else {
            $non_op_time = sprintf("%.${p_dp}f",
                                   $opduration - $p_level_totals[$oplevel]);
            if ($opname =~ /\w{1,3}_OP_(.*)/) {
               $non_op_name = "VRT_OP_$1";
            } else {
               $non_op_name = "VRT_OP_$opname";
            }
            # Non-ops have no 'buckets', so set bucket_id = 0 ...
            $non_op_aggr_key = "$prg_name+$non_op_name+$opflags+$op_source+0";
         }
      }

      #
      # If we're in verbose mode, print details. The non-opcode time will
      # be printed as though it were a normal opcode call.
      #
      if ($p_verbose && $filt_val >= 0 && $opname ne "VRT_OP_ELAPSED") {
         $tstamp = time_string ($optime, 0);

         if ($non_op_name) {
            printf("%s : ", $tstamp);
            for (1..$oplevel) { printf "   "; }
            printf("$non_op_name <$non_op_time, 0, , , %03d/%09d>\n",
                   $oplevel+1, $opid);
         }
         $from_cache =  $cache_calls > 0 ? " - from cache" : "";

         printf("%s : ", $tstamp);
         for (1..$oplevel-1) { printf("   "); }
         printf("$opname <$opduration, $rcnt, $fname, $line_no, " .
                "%03d/%09d $from_cache>\n", $oplevel, $opid);
      }
      
      #
      # If we have call-stack information to print ...
      #
      if ($p_call_stack && $filt_val >= 0 && $opname ne "VRT_OP_ELAPSED") {
         if ($non_op_name) {
            for (1..$oplevel) { printf("|  "); }
            printf("$non_op_name <$non_op_time, 0, %03d/%09d>\n",
                   $oplevel+1, $opid);
         }
         for (1..$oplevel-1) { printf("|  "); }

         $from_cache =  $cache_calls > 0 ? " - from cache" : "";

         printf("$opname <$opduration, $rcnt, %03d/%09d $from_cache>\n",
                $oplevel, $opid);
      }

      #
      # Roll-up record counts so that summary records contain the totals. If
      # we're filtering, don't rollup above the filter level.
      #
      for ($i = $oplevel-1; $i >= 0; $i--) {
        $p_level_counts[$i] += $rcnt if ($i+1 >= $p_elapsed_level);
      }

      #
      # Handle storage of data in our trees ...
      #
      if ($opname ne "VRT_OP_ELAPSED" && $p_fp_depth >= $oplevel) {
         #
         # Handle full-path ...
         #
         my $phref = $G_PATH_STACK[$oplevel-1]; # Find "parent" href
         if ($p_full_path) {
            my $aref = $phref->{$aggr_key};
            if (!defined($aref)) {
               die ("Failed to find key[$aggr_key] in hash[$phref]");
            }
            update_opcode_data ($aref, $call_cnt, $opduration, $err_cnt,
                                $p_level_counts[$oplevel-1], $cache_calls,
                                $cache_t, $min_t, $max_t, $u_cpu, $s_cpu,
                                $st_rng_t, $end_rng_t);
         }

         #
         # Handle update of the 'simple' aggregate data ...
         #
         $aref = $G_SIMPLE{$aggr_key};
         update_opcode_data ($aref, $call_cnt, $opduration, $err_cnt,
                             $p_level_counts[$oplevel-1], $cache_calls,
                             $cache_t, $min_t, $max_t, $u_cpu, $s_cpu,
                             $st_rng_t, $end_rng_t);

         #
         # If we need to handle non-opcode timing as virtual 'CPU' time ...
         # This inserted as a 'virtual' opcode call 'below' the current
         # opcode that's finishing.
         #
         if ($non_op_name) {
            #
            # Full-path aggregate ...
            #
            if ($p_full_path) {
               $aref = $phref->{$aggr_key};
               my $nop_aref = $aref->[AGG_SUB_OPCODES_IDX]->{$non_op_name};
               if (!defined($nop_aref)) {
                  $nop_aref = init_opcode_data ($non_op_name, "", $prg_name, 0,
                                                "", 0);
                  $aref->[AGG_SUB_OPCODES_IDX]->{$non_op_name} = $nop_aref;
               }
               update_opcode_data ($nop_aref, $call_cnt, $non_op_time, 0,
                                   0, 0, 0, 0, 0, 0, 0, "", "");
            }
          
            #
            # Simple aggregates ...
            #
            $nop_aref = $G_SIMPLE{$non_op_aggr_key};
            if (!defined($nop_aref)) {
               $nop_aref = init_opcode_data ($non_op_name, $op_source,
                                             $prg_name, $opflags, "", 0);
               $G_SIMPLE{$non_op_aggr_key} = $nop_aref;
            }
            update_opcode_data ($nop_aref, $call_cnt, $non_op_time, 0,
                                0, 0, 0, 0, 0, 0, 0, "", "");
         }

         #
         # If we need to handle CM transaction cache data ... This is
         # represented as a subordinate opcode to the main one in the
         # full-path, and will be represented as a new opcode for the simple
         # call-stack.
         #
         if ($p_cache && $cache_calls > 0) {
            my $txn_opname = $opname . CM_TXN_OPNAME;
            my $txn_aggr_key = "$prg_name+$opname+$txn_opname+$opflags+" .
                               "$op_source+0";
            #
            # Full-path aggregate ... the *TXN* opcode is inserted under
            # the current one.
            #
            if ($p_full_path) {
               $aref = $phref->{$aggr_key};
               my $txn_aref = $aref->[AGG_SUB_OPCODES_IDX]->{CM_TXN_OPNAME};
               if (!defined($txn_aref)) {
                  $txn_aref = init_opcode_data (CM_TXN_OPNAME, $op_source,
                                                $prg_name, $opflags, $obj_type,
                                                0);
                  $aref->[AGG_SUB_OPCODES_IDX]->{CM_TXN_OPNAME} = $txn_aref;
               }
               update_opcode_data ($txn_aref, $call_cnt, $cache_t, 0,
                                   0, 0, 0, 0, 0, 0, 0, $st_rng_t, $end_rng_t);
            }
          
            #
            # Simple aggregates ...
            #
            $txn_aref = $G_SIMPLE{$txn_aggr_key};
            if (!defined($txn_aref)) {
               $txn_aref = init_opcode_data ($txn_opname, $op_source,
                                             $prg_name, $opflags, $obj_type,
                                             0);
               $G_SIMPLE{$txn_aggr_key} = $txn_aref;
            }
            update_opcode_data ($txn_aref, $cache_calls, $cache_t, 0,
                                0, 0, 0, 0, 0, 0, 0, $st_rng_t, $end_rng_t);
         }
      }

      #
      # If this is a top-level opcode (level 1, or top-level of filter) then
      # track the total elapsed time spent in opcodes. This can be compared
      # with the total elapsed time to exclude time spent 'waiting' between
      # opcode calls... e.g. a client app may not call opcodes so a
      # performance problem could be there and not in BRM.
      #
      if (!$bucket_id && $opname !~ /VRT_OP/) {
         $opcode_elapsed_t += $opduration if ($oplevel == $p_elapsed_level);
         # Base opcode ...
         if (opcode_is_base($opname) && $oplevel <= $p_fp_depth) {
            $_opbase_tot_count += $call_cnt;
            $baseop_elapsed_t += $opduration;
         }
      }

      #
      # Add the total duration of this opcode to the totals for the calling
      # opcode.
      #
      $p_level_totals[$oplevel-1] += $opduration if ($oplevel > 0);
   } elsif ($opstatus eq "S") {
      #
      # Start record:
      #
      # Register this start record at this level by pushing it onto the stack.
      # If it's a level 0 record related to the VRT_OP_ELAPSED "virtual opcode
      # call" we just need to record the start time ... we don't bother with
      # the other stuff.
      #
      if ($opname eq "VRT_OP_ELAPSED") {
         $elapsed_start_t = $optime;
         return;
      } else {
         push (@_optime, $optime);
      }

      #
      # Find opcode in the hash for this part of the tree. If we can't find
      # this opcode, it must be new. So create the placeholder record for it
      # and pop this opcode onto the stack. If we're truncating at a particular
      # depth, don't record opcodes below this level.
      #
      if ($p_fp_depth >= $oplevel) {
         my $phref = $G_PATH_STACK[$oplevel-1]; # Find "parent" href
         my $aref = $phref->{$aggr_key};
         if (!defined($aref)) {
            $aref = init_opcode_data ($opname, $op_source, $prg_name, $opflags,
                                      $obj_type, $bucket_id);
            $phref->{$aggr_key} = $aref;
         }
         $G_PATH_STACK[$oplevel] = $aref->[AGG_SUB_OPCODES_IDX];

         #
         # Simple aggregate initialisation ... 
         #
         my $aref = $G_SIMPLE{$aggr_key};
         if (!defined($aref)) {
            $aref = init_opcode_data ($opname, $op_source, $prg_name, $opflags,
                                      $obj_type, $bucket_id);
            $G_SIMPLE{$aggr_key} = $aref;
         }
      }

      #
      # Print verbose information ...
      #
      if ($p_verbose) {
         if (!$verbose_call_history_header_done) {
            printf("\n");
            printf("Verbose call history\n");
            printf("====================\n\n");
            $verbose_call_history_header_done = 1;
         }
         $tstamp = time_string ($optime, 0);
         printf("%s : ", $tstamp);
         for (1..$oplevel-1) {
            printf("   ");
         }
         #
         # Indicate whether this operation had the transaction flag
         # set - this information is a special case here as this is
         # important when considering performance.
         #
         my $cacheable = $opflags & 0x0400 ? "CACHEABLE" : "";
         my $calc_only = $opflags & 0x0080 ? "CALC_ONLY" : "";

         printf("$opname <flags = 0x%x (%d|$cacheable|$calc_only)>\n",
                $opflags, $opflags);
      }

      #
      # If we have call-stack information to print ...
      #
      if ($p_call_stack) {
         if (!$call_stack_header_done) {
            printf("\n");
            printf("Call-stack history\n");
            printf("==================\n\n");
            $call_stack_header_done = 1;
         }
         for (1..$oplevel-1) { printf("|  "); }
         printf("$opname\n");
      }

      #
      # We have a new opcode so reset the total time for this level and
      # the record counter.
      #
      $p_level_totals[$oplevel] = 0.0;
      $p_level_counts[$oplevel-1] = 0 if ($oplevel > 0);
   } else {
      die ("Bad record status - should be 'S' or 'F'!");
   }
}

#------------------------------------------------------------------------------#
# Function     : print_report_header
#
# Description  : Print basic report header information.
#
# Input        : nfiles     Number of files we've been reporting ...
#
# Output       : None
#
# Return       : None
#------------------------------------------------------------------------------#
sub print_report_header {
   my ($nfiles) = @_;
   my $now = localtime();

   #
   # Print header and input file list ...
   #
   print "#----------------------------------------" .
         "--------------------------------------#\n";
   print "# BRM PERFORMANCE PROFILE\n";
   print "# =======================\n";
   print "#\n";
   print "# Input file(s)   : ";
   for my $i (0..$nfiles-1) {
      print "#                   " if ($i > 0);
      print "$filename[$i]\n";
   }
   print "#\n";

   #
   # Print report options ...
   #
   print "# Report options\n";
   print "# --------------\n";
   print "# Report date     : $now\n";
   print "# Report options  :"; 
   if ($p_verbose) { print " Verbose" }
   if ($p_full_path) { print " Full-Path" }
   if ($p_show_src) { print " (Source)" }
   if ($p_call_stack) { print " Call-Stack" }
   print "\n";
   if ($p_fp_depth && $p_fp_depth != DEPTH_UNLIMITED) {
      printf "#                   Opcode path 'depth' = $p_fp_depth\n";
   }
   if ($#p_filter >= 0 && $p_filter_login) {
      $mfilt = "Filter = $p_filter + Login opcodes";
   } elsif ($#p_filter >= 0) {
      $mfilt = sprintf "Filter = %s", join(".", @p_filter);
   } elsif ($p_filter_login) {
      $mfilt = "Filter = Login opcodes";
   } else {
      $mfilt = "None";
   }
   print "# Filter options  : $mfilt\n";
   if ($p_full_path_start > 0) {
      print "#                   Filter opcodes aren't recorded in 'path'\n";
   }
   print "#--------------------------------------" .
         "----------------------------------------#\n";
}

#------------------------------------------------------------------------------#
# Function     : usage
#
# Description  : Print usage message and exit ...
#
# Input        : None
#
# Output       : None
#
# Return       : None
#------------------------------------------------------------------------------#
sub usage {
   print STDERR <<XXX;
usage : $CMD [-h] [-d] [-c] [-v] [-b] [-l] [-p|-P] [-s<depth>] [-S]
        $SPC [-f|F<filter>] [-x<file>] [-m<file>] [-r] [-n<dp>] [-N]
        $SPC [-C] [-i<indent>] [-D] [-a<attrs>] [-z<n>] <file> [<file2> ...]

where : -h            This 'help' message

        -d            Print debug information to STDERR as we go.

        -D            Use old 'dot-style' format for summary reports

        -i<indent>    Define the indentation level for summary reports (it is 3
                      characters by default).

        -s<depth>     Print additional summary output showing the hierachical
                      relationships between opcodes (their "path", if you like).
                      The option can be qualified with a 'depth' to which
                      detail will be recorded - i.e. at which the opcode 'path'
                      info. is truncated.
                      E.g. -s3 will print full-path summary (to a depth of 3
                           levels)

        -S            Show source-code file and line number references with the
                      opcode information (to distinguish same opcode calls).

        -c            Call stack showing opcode relationships (can't use with
                      verbose option).

        -v            Verbose output. This will print the entire opcode call
                      history with individual timings.

        -b            Show opcode "buckets" (if there were any in the trace
                      file). Opcode buckets are the sub-divisions of opcode
                      timings into specific time ranges.

        -l            Filter login/logout opcodes PCM_OP_ACT_LOGIN and
                      PCM_OP_ACT_LOGOUT

        -p            Add 'process' time to the report. This is the time an
                      opcode spends not executing opcodes (i.e. normal data
                      processing). This is tracked using 'virtual' opcodes in
                      the reports.

        -P            Same as -p option but also adds 'virtual' entries for
                      base opcodes. This generally just clutters up the report
                      but could be useful if opcodes like
                      PCM_OP_TRANS_POL_COMMIT are being used.

        -f|F<filter>  String to filter the "opcode path" to allow us to
                      retrieve information on a particular opcode (useful for
                      getting percentage information for a particular opcode).
                      If -F (upper-case) then call-stack information will
                      exclude the initial filtered path information (i.e. a
                      more readable result).

        -x<file>      Filename for CSV data suitable for use with Excel.

        -m<file>      Mapping file for opcode names (if they're not in the
                      report, which can be the case for custom opcodes
                      depending on the system configuration)

        -r            Remove "PCM_OP" from the opcode names - this helps to
                      "narrow" the report.

        -n<dp>        Number of decimal places to report times to (default is 6)

        -N            Do not print the single-opcode totals when using summary
                      mode reporting.

        -C            Show calls that were returned by the CM transaction
                      cache rather than the dm_oracle.

        -z<n>         Show progress (print on STDERR every 'n' lines)

        -a<attrs>     List of attributes to print in the report. Each letter is
                      a column (they can appear in any order and repeat). The
                      default format is: "otpceamxr". The following values may
                      be used:
                         a  - (a)verage time
                         o  - (o)pcode name
                         c  - number of (c)alls (or executions if you prefer)
                         e  - (e)errors
                         f  - opcode (f)lags
                         m  - (m)inimum execution time
                         p  - (p)ercentage of total time
                         P  - (P)rogram name
                         O  - (O)bject type
                         r  - (r)ecords retrieved
                         s  - (s)ource code reference
                         t  - (t)otal time
                         x  - ma(x)imum execution time
                         U  - (U)ser CPU time
                         S  - (S)ystem CPU time

        <file>        Source data file(s) (or '-' to read from STDIN)
XXX
   exit(1);
}

#------------------------------------------------------------------------------#
# Function     : load_opcode_name_map
#
# Description  : Load the opcode name map for converting opcode numbers to names
#
# Input        : fname    File name
#
# Output       : map_ref  Hash map reference
#
# Return       : 1 if OK, 0 otherwise
#------------------------------------------------------------------------------#
sub load_opcode_name_map {
   my ($fname, $map_ref) = @_;

   if (!open (F, "<$fname")) {
      printf STDERR "ERROR: Failed opening opcode map file '$fname'\n";
      return 0;
   }
   while (<F>) {
      my ($opcode, $opname) = split (/\s+/);
      $map_ref->{$opcode} = $opname;
   }
   close (F);
   return 1;
}

#------------------------------------------------------------------------------#
# Function     : opcode_name
#
# Description  : Determine the opcode name given the trace file entry.
#                Also handle removal of PCM_OP_ etc. if required.
#
# Input        : map_ref   Name reference
#                opcode    Opcode number
#                opname    Opcode name
#
# Output       : None
#
# Return       : Name string to use in report
#------------------------------------------------------------------------------#
sub opcode_name {
   my ($map_ref, $opcode, $opname) = @_;

   $opname = "OP_$opcode" if (!$opname || $opname eq "unknown_operation");
   if (exists($map_ref->{$opname})) {
      $opname = $map_ref->{$opname};
   }
   if ($p_remove_pcm_op) {
      $opname =~ s/^PCM_OP_//;
   }

   return $opname;
}

#------------------------------------------------------------------------------#
# Function     : opcode_is_base
#
# Description  : Is this a base opcode?
#
# Input        : opname   Opcode Name
#
# Output       : None
#
# Return       : 1 if opname is a base opcode, 0 otherwise
#------------------------------------------------------------------------------#
sub opcode_is_base {
   my ($opname) = @_;

   if ($p_remove_pcm_op) {
      return exists($BASE_OPCODES{"PCM_OP_$opname"}) ? 1 : 0;
   } else {
      return exists($BASE_OPCODES{$opname}) ? 1 : 0;
   }
}

#------------------------------------------------------------------------------#
# Function     : validate_report_columns
#
# Description  : Check whether the list of strings provided as columns for the
#                report is valid.
#
# Input        : str      Report column options string
#
# Output       : sp_ref   Show program reference (set to 1 if we have program
#                         name to display)
#                of_ref   Show opcode flags reference
#                src_ref  Show source code
#                obj_ref  Show object type
#
# Return       : 1 if OK, 0 if failure
#------------------------------------------------------------------------------#
sub validate_report_columns {
   my ($str, $sp_ref, $of_ref, $src_ref, $obj_ref) = @_;

   foreach my $opt (split(//, $str)) {
      if (!exists($col_attributes{$opt})) {
         printf STDERR "validate_report_columns : option '%s' is not valid\n",
            $opt;
         return 0;
      }
      $$sp_ref = 1 if ($opt eq "P");  # Program name
      $$of_ref = 1 if ($opt eq "f");  # Opcode flags
      $$src_ref = 1 if ($opt eq "s"); # Source code
      $$obj_ref = 1 if ($opt eq "O"); # Object type
   }
   return 1;
}

#------------------------------------------------------------------------------#
# Function     : print_header
#
# Description  : Print the column headers ...
#
# Input        : astr     Attributes string ...
#                xl       Excel file handle, if Excel
#
# Output       : None
#
# Return       : None
#------------------------------------------------------------------------------#
sub print_header {
   my ($astr, $xl) = @_;

   my $i = 0;
   printf $xl "Report Type,Record ID" if (defined($xl));
   foreach my $opt (split(//, $astr)) {
      my $a = $col_attributes{$opt};
      if (defined($xl)) {
         printf $xl ",";
         printf $xl "%s", $a->{name};
      } else {
         printf "  " if ($i > 0);
         if ($a->{justification} eq "R") {
            printf "%.*s", $a->{len} - length($a->{name}), " " x 100;
         }
         printf "%s", $a->{name};
         if ($a->{justification} eq "L") {
            printf "%.*s", $a->{len} - length($a->{name}), " " x 100;
         }
      }
      $i++;
   }
   if (defined($xl)) {
      printf $xl "\n";
   } else {
      printf "\n";
   }
}

#------------------------------------------------------------------------------#
# Function     : print_underline
#
# Description  : Print the underline headers ...
#
# Input        : astr     Attributes string ...
#
# Output       : None
#
# Return       : None
#------------------------------------------------------------------------------#
sub print_underline {
   my ($astr) = @_;

   my $i = 0;
   foreach my $opt (split(//, $astr)) {
      printf "  " if ($i++ > 0);
      my $a = $col_attributes{$opt};
      if ($a->{justification} eq "R") {
         printf "%.*s", $a->{len} - length($a->{name}), " " x 100;
      }
      printf "%.*s", length($a->{name}), "-" x 100;
      if ($a->{justification} eq "L") {
         printf "%.*s", $a->{len} - length($a->{name}), " " x 100;
      }
   }
   printf "\n";
}

#------------------------------------------------------------------------------#
# Function     : Main
#
# Description  : Not really a function, but rather the entry point for the
#                program to parse results generated by the performance library.
#
# Input        : None  - See "usage" function for details ...
#
# Output       : None
#
# Return       : 0 if OK, non-zero otherwise
#------------------------------------------------------------------------------#
$CMD = basename ($0);      # Command name stripped of any path ...
$SPC = $CMD; $SPC =~ s/./ /g;
%opcodes_used = ();        # Which opcodes have we used?
$p_debug = 0;              # Debug information ...
$p_verbose = 0;            # Verbose mode - print the detailed opcode stack
$p_full_path = 0;          # Full-path summary
$p_full_path_start = 0;    # Level at which full_path results are printed
                           # (we can choose to exclude superfluous information
                           #  when filtering)
$p_show_src = 0;           # Show source-code references? Default is no.
$p_call_stack = 0;         # Print call stack information ...
$p_fp_depth = DEPTH_UNLIMITED;  # Maximum depth at which to print opcode 'path'
$_max_len_single = 15;     # Length of longest single opcode string
$_max_len_composite = 15;  # Length of longest composite opcode string
$_max_len_prog = 0;        # Length of longest program name
$_max_len_obj_type = 0;    # Length of longest object type
$_max_len_src = 0;         # Length of longest src reference 
@p_filter = ();            # Filter list for opcodes
$p_filter_type = "";       # What type of filtering are we applying ...
$is_filtered = 1;          # Are we currently filtering? Default is yes ...
$p_excel = "";             # Excel (CSV) file output
$p_elapsed_level = 1;      # Level at which elapsed times are taken (usually 1
                           # but can be greater if filtering at a lower level)
$p_filter_login = 0;       # Filter PCM_OP_ACT_LOGIN / PCM_OP_ACT_LOGOUT ...
$p_buckets = 0;            # Do we print sub buckets for opcodes?
$p_opmap_f = "";           # Opcode map file
%p_opmap = ();             # Opcode map hash
@p_level_totals = ();      # Counts the totals of calls at each level - used to
                           # calculate the time spent doing non-opcode stuff in
                           # an opcode.
@p_level_counts = ();      # Count the total records at each level ..
$p_rpt_non_op = 0;         # Do we record non-opcode time in the reports?
$p_remove_pcm_op = 0;      # Do we remove PCM_OP_ from the opcode names?
$p_dp = 6;                 # Default to reporting times in micro-seconds
$p_cache = 0;              # Show CM transaction cache information ...
$p_indent_size = 3;        # Default to 3 "|  "
$p_indent_str = "|  ";     # Indent string
$p_dot_style = 0;          # Use old 'dot-style' output ...
$has_opt_a = 0;            # No custom attributes
$p_attributes = "otpceamxr"; # opcode/total/pct/calls/errors/avg/min/max/recs
$p_show_prog = 0;          # Show program in report?
$p_show_obj_type = 0;      # Show object type in report?
$p_show_opflags = 0;       # Show opcode flags in report?
$p_show_progress = 0;      # Show progress on STDERR
$p_trace_version = 0;      # Trace file version ...
$p_no_single = 0;          # No single opcode report (only in summary mode)

#
# Login filter 'paths' ...
#
@LOGIN_FILTER = ( [ "ACT_LOGIN" ], [ "ACT_LOGOUT" ], [ "ACT_FIND_VERIFY" ] );
@login_filter = ( [ "PCM_OP_ACT_LOGIN" ], [ "PCM_OP_ACT_LOGOUT" ],
                  [ "PCM_OP_ACT_FIND_VERIFY" ] );

#
# Hash of data ...
#
%G_FULL_PATH = ();
%G_SIMPLE = ();
@G_PATH_STACK = ();
@G_FILTER_STACK = ();
push (@G_PATH_STACK, \%G_FULL_PATH);  # 0th entry is always the "root"

#
# Parse options and arguments ...
#
getopts('a:hdcCvlpPf:F:s:Sx:X:m:brn:i:Dz:N', \%opt) or usage();
if ($opt{h}) { usage() }
if ($opt{d}) { $p_debug = 1 }
if ($opt{v}) { $p_verbose = 1 }
if ($opt{c}) { $p_call_stack = 1 }
if ($opt{C}) { $p_cache = 1 }
if ($opt{D}) { $p_dot_style = 1 }
if (length($opt{s}) > 0) {
   $p_full_path = 1;
   $p_fp_depth = $opt{s} > 0 ? $opt{s} : DEPTH_UNLIMITED;
}
if ($opt{S}) { $p_show_src = 1 }
if ($opt{f} || $opt{F}) {
   if ($opt{f}) {
      $p_filter_type = "f";
   } else {
      $p_filter_type = "F";
   }
   @p_filter = split(/[.]/, $opt{$p_filter_type});
   $p_elapsed_level = scalar(@p_filter);
   $p_full_path_start = $p_elapsed_level-1 if ($opt{F});
}
if ($opt{x}) { $p_excel = $opt{x} }
if ($opt{l}) { $p_filter_login = 1; }
if ($opt{m}) {
   $p_opmap_f = $opt{m};
   if (!load_opcode_name_map ($p_opmap_f, \%p_opmap)) {
      printf STDERR "ERROR: Failed loading opcode map file\n";
      exit(1);
   }
}
if ($opt{b}) { $p_buckets = 1 }
if ($opt{p}) { $p_rpt_non_op = 1 }
if ($opt{P}) { $p_rpt_non_op = 2 }  # Include VRT_ times for base opcodes
if ($opt{r}) { $p_remove_pcm_op = 1 }
if ($opt{n}) { $p_dp = $opt{n} }    # Decimal place ...
$p_nw = 8 + $p_dp;                  # Numeric width
if ($opt{i}) {
   $p_indent_size = $opt{i};
   if ($p_indent_size < 2) {
      $p_indent_str = " ";
   } else {
      $p_indent_str = "|" . (" " x ($p_indent_size-1));
   }
}
if ($opt{a}) {
   $has_opt_a = 1;
   $p_attributes = $opt{a}
}
if ($opt{z}) { $p_show_progress = $opt{z} }
if ($opt{N}) { $p_no_single = 1 }

#
# Check option combinations
#
if ($p_verbose && $p_call_stack) {
   print STDERR "Cannot use -c and -v options together\n";
   usage();
}
if ($p_dot_style && $opt{i}) {
   print STDERR "Cannot use -D and -i options together\n";
   usage();
}

if ($has_opt_a && $p_show_src) {
   printf STDERR "-S option should not be used with -a option\n";
   printf STDERR "You may add 's' to the -a list of attributes\n";
   usage();
} elsif ($p_show_src) {
   # opcode/source/total/calls/errors/average/min/max/records
   $p_attributes = "ostpceamxr";
}

if ($p_no_single && !$p_full_path) {
   printf STDERR "-N option must only be used with summmary (-s) mode\n";
   usage();
}

#
# Define and validate columns in the report ... This MUST be after the
# $p_dp setting is retrieved ...
#
# Column descriptions, lengths, formatting definitions etc. The hfmt is for
# header formatting, the dfmt for data-formatting, the xfmt for excel output
# formatting.
#
# NOTE: The length of the opcode name, program name and source will be
#       calculated based on the data present in the report.
#
%col_attributes = (
   "o" => { name => "Opcode Name",
            hfmt => '%-*.*s',
            dfmt => '%-*.*s',
            xfmt => "%s",
            len => 12,
            justification => "L",
   },
   "f" => { name => "OpFlags",
            hfmt => "%#10x",
            dfmt => "%#10x",
            xfmt => "%#x",
            len => 10,
            justification => "R",
   },
   "O" => { name => "Object Type",
            hfmt => '%-*.*s',
            dfmt => '%-*.*s',
            xfmt => "%s",
            len => 12,
            justification => "L",
   },
   "P" => { name => "Program",
            hfmt => '%-*.*s',
            dfmt => '%-*.*s',
            xfmt => "%s",
            len => 8,
            justification => "L",
   },
   "t" => { name => "Total",
            hfmt => "%${p_nw}s",
            dfmt => "%${p_nw}.${p_dp}f",
            xfmt => "%.${p_dp}f",
            len => ${p_nw},
            justification => "R",
   },
   "p" => { name => "%age",
            hfmt => "%6s",
            dfmt => "%6.2f",
            xfmt => "%.2f",
            len => 6,
            justification => "R",
   },
   "c" => { name => "Calls",
            hfmt => "%8s",
            dfmt => "%10d",
            xfmt => "%d",
            len => 10,
            justification => "R",
   },
   "e" => { name => "Errors",
            hfmt => "%8s",
            dfmt => "%8d",
            xfmt => "%d",
            len => 8,
            justification => "R",
   },
   "a" => { name => "Average",
            hfmt => "%${p_nw}s",
            dfmt => "%${p_nw}.${p_dp}f",
            xfmt => "%.${p_dp}f",
            len => ${p_nw},
            justification => "R",
   },
   "m" => { name => "Minimum",
            hfmt => "%${p_nw}s",
            dfmt => "%${p_nw}.${p_dp}f",
            xfmt => "%.${p_dp}f",
            len => ${p_nw},
            justification => "R",
   },
   "x" => { name => "Maximum",
            hfmt => "%${p_nw}s",
            dfmt => "%${p_nw}.${p_dp}f",
            xfmt => "%.${p_dp}f",
            len => ${p_nw},
            justification => "R",
   },
   "r" => { name => "Records",
            hfmt => "%10s",
            dfmt => "%10d",
            xfmt => "%d",
            len => 10,
            justification => "R",
   },
   "s" => { name => "Source",
            hfmt => '%-*.*s',
            dfmt => '%-*.*s',
            xfmt => "%s",
            len => 10,
            justification => "L",
   },
   "U" => { name => "User CPU",
            hfmt => "%${p_nw}s",
            dfmt => "%${p_nw}.${p_dp}f",
            xfmt => "%.${p_dp}f",
            len => ${p_nw},
            justification => "R",
   },
   "S" => { name => "System CPU",
            hfmt => "%${p_nw}s",
            dfmt => "%${p_nw}.${p_dp}f",
            xfmt => "%.${p_dp}f",
            len => ${p_nw},
            justification => "R",
   },
);

if (!validate_report_columns($p_attributes, \$p_show_prog, \$p_show_opflags,
                             \$p_show_src, \$p_show_obj_type))
{
   usage();
}

#
# Check arguments - we expect one or more filenames ...
#
usage() if $#ARGV < 0;

#
# Variables ...
#
$elapsed_t = 0;
$opcode_elapsed_t = 0;
$baseop_elapsed_t = 0;

$p_total_files = scalar(@ARGV);
$fno = 0;

#
# We can't produce verbose or call-stack reports (only summary stuff) if we're
# processing multiple files ...
#
if ($p_total_files > 1 && ($p_verbose || $p_call_stack)) {
   printf STDERR "ERROR: Multiple files only allowed in summary mode.\n\n";
   usage();
}

#
# Parse filenames and check some basic information - this is to ensure
# that if we have multiple files that we're not aggregating report data
# for CMs and DMs etc.
# 
printf STDERR "$CMD : Started at %s ...\n", localtime()."" if ($p_debug);
printf STDERR "$CMD : Checking files ...\n" if ($p_debug);

foreach $fno (0..$p_total_files-1) {
   $filename = $ARGV[$fno];
   if ($filename =~ /^.*\.plog\.txt$/ or $filename eq "-") {
      $filename[$fno] = $filename;
   } else {
      print STDERR
         "ERROR: Filename '$filename' doesn't conform to naming convention!\n";
      exit(1);
   }
}

#
# Do the parsing of the report ... Read all files into memory in aggregated
# form ready for aggregation and formatting.
#
printf STDERR "$CMD : Processing files ...\n" if ($p_debug);

print_report_header ($p_total_files);

foreach $fno (0..$p_total_files-1) {
   #
   # Open file and parse all data ...
   #
   $rownum = 0;
   $start_t = 0;
   $is_filtered = 1;
   my $rec_id = 0;

   printf STDERR "$CMD : Processing file $filename ...\n" if ($p_debug);

   if ($filename[$fno] ne "-") {
      open (STDIN, "<$filename[$fno]") or
         die ("Failed opening '$filename[$fno]'");
   }
   my @rec_stack = ();
   while (<STDIN>) {
      chomp;
      $rec_id += 1;

      #
      # If this is a start record, stack it for use with the matching 
      # finish record.
      #
      my @data = split(/,/, $_);
      if ($data[0] eq "S") {
         push (@rec_stack, \@data);
         process_data_row ($fno, $rec_id,
                           "S",         # start/finish
                           $data[1],    # level
                           $data[2],    # opid / sequence number
                           $data[3],    # opcode
                           $data[4],    # opcode flags
                           $data[5],    # opcode name
                           $data[6],    # timestamp
                           $data[7],    # filenmae
                           $data[8],    # line number
                           $data[9],    # PID
                           $data[10],   # TID
                           0,           # record count
                           0,           # call count
                           0,           # min time
                           0,           # max time
                           $data[12],   # bucket ID
                           0,           # bucket Start range
                           0,           # bucket end range
                           0,           # cache calls
                           0,           # cache time
                           0,           # error count
                           0,           # user CPU
                           0,           # system CPU
                           $data[11],   # program name
                           $data[13]);  # object type

      } else {
         my $aref = pop(@rec_stack);
         process_data_row ($fno, $rec_id,
                           "F",         # start/finish
                           $$aref[1],   # level
                           $$aref[2],   # opid / sequence number
                           $$aref[3],   # opcode
                           $$aref[4],   # opcode flags
                           $$aref[5],   # opcode name
                           $data[1],    # timestamp
                           $$aref[7],   # filenmae
                           $$aref[8],   # line number
                           $$aref[9],   # PID
                           $$aref[10],  # TID
                           $data[2],    # record count
                           $data[3],    # call count
                           $data[4],    # min time
                           $data[5],    # max time
                           $$aref[12],  # bucket ID
                           $data[6],    # bucket Start range
                           $data[7],    # bucket end range
                           $data[8],    # cache calls
                           $data[9],    # cache time
                           $data[10],   # error count
                           $data[11],   # user CPU
                           $data[12],   # system CPU
                           $$aref[11],  # program name
                           $$aref[13]); # object type

      }

      # Show progres ...
      if ($p_show_progress > 0 && $rec_id > 0 &&
          ($rec_id % $p_show_progress) == 0)
      {
         printf STDERR "%s : processed $rec_id lines\n", localtime() . "";
      }
   }
}

#
# Print report details ...
#
if ($p_excel) {
   open ($xlf, ">$p_excel") or die ("Failed creating file '$p_excel'");
}

printf STDERR "$CMD : Printing report ...\n" if ($p_debug);

print_reports ($elapsed_t, $opcode_elapsed_t, $baseop_elapsed_t,
               $p_total_files);

close ($xlf) if ($p_excel);

printf STDERR "$CMD : Finished at %s\n", localtime()."" if ($p_debug);
exit(0);

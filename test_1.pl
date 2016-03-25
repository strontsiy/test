package test_1;

use strict;
use warnings;

sub rsort {
    my ($ar_ref, $as_string) = @_;
    return ( $as_string ? sort { $b cmp $a } @$a : sort { $b <=> $a } @$ar );
}

1;

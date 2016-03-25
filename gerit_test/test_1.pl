package test_1;

use strict;
use warnings;

sub sort_array_desc {
    my $ar = shift;
    return sort { $b <=> $a } @$ar;
}

1;

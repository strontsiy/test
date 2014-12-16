#!/usr/bin/perl

use strict;
use warnings;
use DBI;
use CGI qw(:standard escapeHTML);
use CGI::Carp;
use PDL;
use PDL::Matrix;
use PDL::MatrixOps;

sub transponirovat {
    my $m = shift;
    my @matrix = @{$m};
    my @matrix_tr = ();
    for my $row (0..$#matrix) {
        for my $col (0..2) {
            $matrix_tr[$col][$row] = $matrix[$row][$col];
        }
    }
    return @matrix_tr;
}

sub mult {
    my ($m1, $m2) = @_;
    my @matrix1 = @{$m1};
    my @matrix2 = @{$m2};
    my @matrix = ();
    my ($rowsum, $colsum) = (0 , 0);
    for (0..(@matrix1 * @matrix1 - 1)) {
        my $row = $_ / @matrix1;
        my $col = $_ % @matrix1;
        for (0..$#matrix2) {
            $matrix[int($row)][$col] += $matrix1[int($row)][$_] * $matrix2[$_][$col] ;
        }
    }
    return @matrix;
}

sub viznachnik {
    my $m = shift;
    my @matrix = @{$m};
    my $d = ($m->[0]->[0] * $m->[1]->[1] * $m->[2]->[2])
            - ($m->[0]->[2] * $m->[1]->[1] * $m->[2]->[0])
            - ($m->[0]->[1] * $m->[1]->[2] * $m->[2]->[0])
            - ($m->[0]->[2] * $m->[1]->[0] * $m->[2]->[1])
            + ($m->[0]->[0] * $m->[1]->[2] * $m->[2]->[1])
            + ($m->[0]->[1] * $m->[1]->[0] * $m->[2]->[2]);
    return $d;
}

sub rkj {
    my ($k, $j, $inv_matrix) = @_;
    my $r = (-$inv_matrix->index2d($k,$j)) / sqrt($inv_matrix->index2d($k,$k) * $inv_matrix->index2d($j,$j));
    return $r;
}

my $dsn = 'DBI:mysql:Empir:localhost';
my $db_user_name = 'root';
my $db_password = '955742';
my ($id, $password);
my $dbh = DBI->connect($dsn, $db_user_name, $db_password);

my $sql = "SELECT * FROM proc_optim ORDER BY id";
my $sth = $dbh->prepare($sql);
$sth->execute;
my @table = @{$sth->fetchall_arrayref};
my @matrix = ();
for my $row (0..$#table){
    $matrix[$row][0] = $table[$row][2];
    $matrix[$row][1] = $table[$row][3];
    $matrix[$row][2] = $table[$row][4];
}
my @matrix_tr = transponirovat(\@matrix);
@matrix = mult(\@matrix_tr, \@matrix);
my $descr = viznachnik(\@matrix);
my $x_kv = -(@matrix - 1 - 1/2*(2*3+5)) * log($descr);


#-- start html
print header (-charset => 'UTF-8'), start_html();
print "<link rel=stylesheet type=text/css href=style.css />";
print "<link rel=stylesheet type=text/css href=mystyle.css />";
print "<table class='pure-table pure-table-bordered pure-table-striped' style='margin: 30px auto;'>";
print '<tr>', 
        td('id'), td('name'), td('frequency'), 
        td('cache'), td('speed'), td('price'),
      '</tr>';
for my $arref (@table){
    print '<tr>';
    for (0..$#{$arref}){
        if ($_ != 0 && $_ != 1) {
            print td(sprintf("%.5f", $arref->[$_]));
        }
        else {
            print td($arref->[$_]);
        }
    }
    print '</tr>';
}
print '</table>';
print "<table class='pure-table pure-table-bordered pure-table-striped' style='margin: 30px auto;'>";
for my $arref (@matrix){
    print '<tr>';
    for (0..$#{$arref}){
        print td(sprintf("%.5f", $arref->[$_]));
    }
    print '</tr>';
}
print '</table>';
print div("x_kv = $x_kv");
my $pdl_matrix = pdl \@matrix;
my $inv_matrix = $pdl_matrix->inv;
print "<table class='pure-table pure-table-bordered pure-table-striped' style='margin: 30px auto;'>";
for my $row (0..2){
    print '<tr>';
    for my $col (0..2){
        print td(sprintf("%.5f", $inv_matrix->index2d($row,$col)));
    }
    print '</tr>';
}
print '</table>';
my $f11 = ($inv_matrix->index2d(0,0) - 1) * 86 / 2;
my $f22 = ($inv_matrix->index2d(1,1) - 1) * 86 / 2;
my $f33 = ($inv_matrix->index2d(2,2) - 1) * 86 / 2;
print '<div>';
    print "F11 = $f11<br>";
    print "F22 = $f22<br>";
    print "F33 = $f33<br>";
print '</div>';
print "<table class='pure-table pure-table-bordered pure-table-striped' style='margin: 30px auto;'>";
for my $k (0..2){
    for my $j (0..2){
        print '<tr>';
        print td("t$k$j");
        print td(sprintf("%.5f", rkj($k, $j, $inv_matrix)));
        print '</tr>';
    }
}
print '</table>';
# getero
$sql = "SELECT price FROM proc ORDER BY id";
my $sth = $dbh->prepare($sql);
$sth->execute;
my @table_y = @{$sth->fetchall_arrayref};
my @e;
for (0..88) {
    my $buf = $table[$_][6] - $table_y[$_][0]
}
print end_html();
#-- end html
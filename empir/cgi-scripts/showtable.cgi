#!/usr/bin/perl

use strict;
use warnings;
use DBI;
use CGI qw(:standard escapeHTML);

print header (-charset => 'UTF-8'), start_html("show table");
print "<link rel=stylesheet type=text/css href=style.css />";

my $dsn = 'DBI:mysql:Empir:localhost';
my $db_user_name = 'root';
my $db_password = '955742';
my ($id, $password);
my $dbh = DBI->connect($dsn, $db_user_name, $db_password);
my $sql = "SELECT * FROM proc";
my $sth = $dbh->prepare($sql);
$sth->execute;
# name, frequency, cache, speed, price
my @table = @{$sth->fetchall_arrayref};
$sth->finish;

print "<table class='pure-table pure-table-bordered pure-table-striped' style='margin: 30px auto;'>";
print "<tr>", 
           td("id"), td("name"), td("frequency GHz"), 
           td("cache Mb"), td("speed %"), td("price rub"), td("price/speed"), 
      "</tr>";
my $tsp;
for my $arref(@table){
    print "<tr>";
    for (@{$arref}){
        print td("$_");
    }
    my $sp = $$arref[5] / $$arref[4];
    $tsp += $sp;
    print td(sprintf("%.3f", $sp));
    print "</tr>";
}
$tsp /= @table;
print "<tr>", td("E"), td(), td(), td(), td(), td(), td(sprintf("%.3f", $tsp)), "</tr>";
print "</table>";

print end_html();




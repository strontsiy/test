#!/usr/bin/perl

use strict;
use warnings;
use DBI;
use CGI qw(:standard escapeHTML);
use CGI::Carp;
use Chart::Gnuplot;

sub xsr1 {
    my (@num) = @_;
    my $xsr = 0;
    for (@num){
        $xsr += $_;
    }
    $xsr /= @num;
    return $xsr;
}

sub si_for_r {
    my (@num) = @_;
    my $xsr = xsr1(@num);
    my $sum = 0;
    for (@num){
        $sum += abs($_ - $xsr)**2;
    }
    return sqrt($sum);
}

sub disp {
    my (@num) = @_;
    my $xsr = xsr1(@num);
    my $sum = 0;
    for (@num){
        $sum += abs($_ - $xsr)**2;
    }
    my $d = (1 / @num) * $sum;
    return $d;
}

sub partly_kor {
    my ($x1, $y1) = @_;
    my @x = @{$x1};
    my @y = @{$y1};
    my $si1 = si_for_r(@x);
    my $si2 = si_for_r(@y);
    my $xsr = xsr1(@x);
    my $ysr = xsr1(@y);
    my $r = 0;
    for my $i (0..$#x) {
        $r += ($x[$i] - $xsr) * ($y[$i] - $ysr);
    }
    $r /= $si1 * $si2;
    return $r;
}



sub optim {
    my ($x, $xsr, $disp) = @_;
    my @xn = ();
    for (@{$x}){
        my $opt = ($_ - $xsr) / sqrt(@{$x} * $disp);
        push @xn, $opt;
    }
    return @xn;
}

sub optim_all {
    my ($x11, $x21, $x31, $x41, $x51) = @_;
    my @x1 = @{$x11};
    my @x2 = @{$x21};
    my @x3 = @{$x31};
    my @x4 = @{$x41};
    my @x5 = @{$x51};
    my $x2sr = xsr1(@x2);
    my $x3sr = xsr1(@x3);
    my $x4sr = xsr1(@x4);
    my $x5sr = xsr1(@x5);
    print STDERR "\n$x5sr\n";
    my $disp2 = disp(@x2);
    my $disp3 = disp(@x3);
    my $disp4 = disp(@x4);
    my $disp5 = disp(@x5);
    print STDERR "\n$disp5\n";
    my (@xn2, @xn3, @xn4, @xn5);
    @xn2 = optim(\@x2, $x2sr, $disp2);
    @xn3 = optim(\@x3, $x3sr, $disp3);
    @xn4 = optim(\@x4, $x4sr, $disp4);
    @xn5 = optim(\@x5, $x5sr, $disp5);
    my $dsn = 'DBI:mysql:Empir:localhost';
    my $db_user_name = 'root';
    my $db_password = '955742';
    my ($id, $password);
    my $dbh = DBI->connect($dsn, $db_user_name, $db_password);
    for (0..$#xn2) {
        my $name  = $x1[$_];
        my $freq  = sprintf("%.8f", $xn2[$_]);
        my $cache = sprintf("%.8f", $xn3[$_]);
        my $speed = sprintf("%.8f", $xn4[$_]);
        my $price = sprintf("%.8f", $xn5[$_]);
        my $sql = "INSERT INTO proc_optim (name, frequency, cache, speed, price) "
                 ."VALUES('$name', $freq, $cache, $speed, $price);";
        my $sth = $dbh->prepare($sql);
        $sth->execute;
        $sth->finish;
    }
}

print header (-charset => 'UTF-8'), start_html();
print "<link rel=stylesheet type=text/css href=style.css />";
print "<link rel=stylesheet type=text/css href=mystyle.css />";

my $dsn = 'DBI:mysql:Empir:localhost';
my $db_user_name = 'root';
my $db_password = '955742';
my ($id, $password);
my $dbh = DBI->connect($dsn, $db_user_name, $db_password);
# from frequency, cache, speed, price
my $col = param('col');
my $count = param('count');
#$col = 'frequency';
#$count = '2';
if ($count == 0){
    # 7.44
    $count = 1 + (3.322 * log(89) / log(10));
    $count = int($count);
}

# min and max value
my $sql = "SELECT min($col), max($col) FROM proc";
my $sth = $dbh->prepare($sql);
$sth->execute;
my @minmax = $sth->fetchrow_array;
$sth->finish;

#--

print "<div class='BlockCaption'>Group by $col</div>";
my $grouplen = ($minmax[1] - $minmax[0]) / $count;
my $minlen = $minmax[0]; 
my $n = 1;
my ($chart1, $chart2, $chart3, $dataset1, $dataset2, $dataset3);
my (@y1, @y2, @y3, @y4, @y5, @yhisto, @xhisto);
while ($minlen < $minmax[1]){
    @y1 = (); @y2 = (); @y3 = (); @y4 = (); @y5 = ();
    my $maxlen = $minlen + $grouplen;
    if ($maxlen == $minmax[1]){
        $sql = "SELECT * FROM proc WHERE $col>=$minlen and $col<=$maxlen ORDER BY $col DESC";
    }
    else{
        $sql = "SELECT * FROM proc WHERE $col>=$minlen and $col<$maxlen ORDER BY $col DESC";
    }
    $sth = $dbh->prepare($sql);
    $sth->execute;
    my @table = @{$sth->fetchall_arrayref};
    $sth->finish;
    print div({-align=>'center'}, sprintf("Interval: %.3f", $minlen), " - ", sprintf("%.3f", $maxlen));
    #print div({-align=>'center'}, $minlen, " - ", $maxlen);
    print "<table class='pure-table pure-table-bordered pure-table-striped' style='margin: 30px auto;'>";
    print "<tr>", 
            td("id"), td("name"), td("frequency GHz"), 
            td("cache Mb"), td("speed %"), td("price rub"), td("price/speed"), 
          "</tr>";
    push @xhisto, sprintf("%.2f", $minlen);
    push @yhisto, scalar(@table);
    unless ($table[0][0]){
        print "</table>";
        $minlen = $maxlen;
        next;
    }
    my $tsp = 0;
    my $mf = 0;
    my $mc = 0;
    my $ms = 0;
    my $mp = 0;
    for my $arref (@table){
        print "<tr>";
        for (0..$#{$arref}){
            #print td("$$arref[$_]&nbsp&nbsp");
            print td("$$arref[$_]");
        }
        push @y1, $$arref[1];
        push @y2, $$arref[2];
        push @y3, $$arref[3];
        push @y4, $$arref[4];
        push @y5, $$arref[5];
        $mf += $$arref[2];
        $mc += $$arref[3];
        $ms += $$arref[4];
        $mp += $$arref[5];
        my $sp = $$arref[5] / $$arref[4];
        $tsp += $sp;
        print td(sprintf("%.3f", $sp));
        print "</tr>";
    }
    $mf /= @y2;
    $mc /= @y3;
    $ms /= @y4;
    $mp /= @y5;
    $tsp /= @y4;
    print "<tr>", td("E"), td(), td(sprintf("%.3f", $mf)), td(sprintf("%.3f", $mc)), td(sprintf("%.1f", $ms)), td(sprintf("%.1f", $mp)), td(sprintf("%.3f", $tsp)), "</tr>";
    print "</table>";
    my $num = 0;
    if ($col eq "frequency"){
    	$num = \@y2;
    }
	elsif ($col eq "cache"){
		$num = \@y3;
	}
	elsif ($col eq "speed"){
		$num = \@y4;
	}
	elsif ($col eq "price"){
		$num = \@y5;
	}
	
	# razmer variacii
	my $r = $maxlen - $minlen;
	
	# x(sr)
	my $xsr = 0;
	for (@{$num}){
		$xsr += $_;
	}
	$xsr /= @{$num};

	# sr lineinie
    my $sum = 0;
    for (@{$num}){
    	$sum += abs($_ - $xsr);
    }
    my $a = (1 / @{$num}) * $sum;

    # dispersia 
    $sum = 0;
    for (@{$num}){
    	$sum += abs($_ - $xsr)**2;
    }
    my $d = (1 / @{$num}) * $sum;
    
    # sr kvadratichnoe
    my $si = sqrt($d);

    # r(freequence cache)
    my $r23 = sprintf("%.6f",partly_kor(\@y2, \@y3));
    # r(freequence speed)
    my $r24 = sprintf("%.6f",partly_kor(\@y2, \@y4));
    # r(freequence price)
    my $r25 = sprintf("%.6f",partly_kor(\@y2, \@y5));
    # r(cache speed)
    my $r34 = sprintf("%.6f",partly_kor(\@y3, \@y4));
    # r(cache price)
    my $r35 = sprintf("%.6f",partly_kor(\@y3, \@y5));
    # r(speed price)
    my $r45 = sprintf("%.6f",partly_kor(\@y4, \@y5));

    #optim_all(\@y1, \@y2, \@y3, \@y4, \@y5);

    print "<div>";
    	print "Размах вариации R = $r<br>";
    	print "Среднее линейное отклонение a = $a<br>";
    	print "Дисперсия D = $d<br>";
    	print "Среднее квадратическое отклонение si = $si<br>";
        print "r<font size=1>freeq_cache</font> = $r23<br>";
        print "r<font size=1>freeq_speed</font> = $r24<br>";
        print "r<font size=1>freeq_price</font> = $r25<br>";
        print "r<font size=1>cache_speed</font> = $r34<br>";
        print "r<font size=1>cache_price</font> = $r35<br>";
        print "r<font size=1>speed_price</font> = $r45<br>";
    print "</div>";
    $minlen = $maxlen;
    
    # graphics
    $chart1 = Chart::Gnuplot->new(
        output => "graphics/1$n.png",
        title  => "groupgraphic",
        xlabel => "x",
        ylabel => "y",
        bg     => "white",
    );
    $chart2 = Chart::Gnuplot->new(
        output => "graphics/2$n.png",
        title  => "groupgraphic",
        xlabel => "x",
        ylabel => "y",
        bg     => "white"
    );
    $chart3 = Chart::Gnuplot->new(
        output => "graphics/3$n.png",
        title  => "groupgraphic",
        xlabel => "x",
        ylabel => "y",
        bg     => "white"
    );
    # dataset depending on the column 
    if ($col eq "frequency"){
        $dataset1 = Chart::Gnuplot::DataSet->new(
            xdata => \@y2,
            ydata => \@y3,
            title => "$col depending on the cache",
            style => "linespoints",
        );
        $dataset2 = Chart::Gnuplot::DataSet->new(
            xdata => \@y2,
            ydata => \@y4,
            title => "$col depending on the speed",
            style => "linespoints",
        );
        $dataset3 = Chart::Gnuplot::DataSet->new(
            xdata => \@y2,
            ydata => \@y5,
            title => "$col depending on the price",
            style => "linespoints",
        );
        print "<a class='GraphURLS'  href='graphics/1$n.png'>$col depending on the cache</a>";
        print "<a class='GraphURLS'  href='graphics/2$n.png'>$col depending on the speed</a>";
        print "<a class='GraphURLS'  href='graphics/3$n.png'>$col depending on the price</a>";
    }
    elsif ($col eq "cache"){
        $dataset1 = Chart::Gnuplot::DataSet->new(
            xdata => \@y3,
            ydata => \@y2,
            title => "$col depending on the frequency",
            style => "linespoints",
        );
        $dataset2 = Chart::Gnuplot::DataSet->new(
            xdata => \@y3,
            ydata => \@y4,
            title => "$col depending on the speed",
            style => "linespoints",
        );
        $dataset3 = Chart::Gnuplot::DataSet->new(
            xdata => \@y3,
            ydata => \@y5,
            title => "$col depending on the price",
            style => "linespoints",
        );
        print "<a class='GraphURLS'  href='graphics/1$n.png'>$col depending on the frequency</a>";
        print "<a class='GraphURLS'  href='graphics/2$n.png'>$col depending on the speed</a>";
        print "<a class='GraphURLS'  href='graphics/3$n.png'>$col depending on the price</a>";
    }
    elsif ($col eq "speed"){
        $dataset1 = Chart::Gnuplot::DataSet->new(
            xdata => \@y4,
            ydata => \@y2,
            title => "$col depending on the frequency",
            style => "linespoints",
        );
        $dataset2 = Chart::Gnuplot::DataSet->new(
            xdata => \@y4,
            ydata => \@y3,
            title => "$col depending on the cache",
            style => "linespoints",
        );
        $dataset3 = Chart::Gnuplot::DataSet->new(
            xdata => \@y4,
            ydata => \@y5,
            title => "$col depending on the price",
            style => "linespoints",
        );
        print "<a class='GraphURLS'  href='graphics/1$n.png'>$col depending on the frequency</a>";
        print "<a class='GraphURLS'  href='graphics/2$n.png'>$col depending on the cache</a>";
        print "<a class='GraphURLS'  href='graphics/3$n.png'>$col depending on the price</a>";
    }
    elsif ($col eq "price"){
        $dataset1 = Chart::Gnuplot::DataSet->new(
            xdata => \@y5,
            ydata => \@y2,
            title => "$col depending on the frequencys",
            style => "linespoints",
        );
        $dataset2 = Chart::Gnuplot::DataSet->new(
            xdata => \@y5,
            ydata => \@y3,
            title => "$col depending on the cache",
            style => "linespoints",
        );
        $dataset3 = Chart::Gnuplot::DataSet->new(
            xdata => \@y5,
            ydata => \@y4,
            title => "$col depending on the speed",
            style => "linespoints",
        );
        print "<a class='GraphURLS'  href='graphics/1$n.png'>$col depending on the frequency</a>";
        print "<a class='GraphURLS'  href='graphics/2$n.png'>$col depending on the cache</a>";
        print "<a class='GraphURLS'  href='graphics/3$n.png'>$col depending on the speed</a>";
    }
    eval {
        $chart1->plot2d($dataset1); 
        $chart2->plot2d($dataset2);
        $chart3->plot2d($dataset3);
    }; 
    if ($@){
        print ("problem with gnuplot");
        die;
    };
    $n++;
}
my $chart = Chart::Gnuplot->new(
        output => "graphics/histo.png",
        title  => "grouphisto",
        xlabel => "x",
        ylabel => "y",
        bg     => "white",
        #"style histogram" => "rowstacked",
    );
my $dataset = Chart::Gnuplot::DataSet->new(
        xdata => \@xhisto,
        ydata => \@yhisto,
        title => "histo for group",
        style => "histograms",
        #fill => {density => 1},
        #boxwidth => 50,
   );
$chart->plot2d($dataset);
print end_html();

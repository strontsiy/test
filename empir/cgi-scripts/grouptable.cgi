#!/usr/bin/perl

use strict;
use warnings;
use DBI;
use CGI qw(:standard escapeHTML);
use CGI::Carp;
use Chart::Gnuplot;

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
my (@y2, @y3, @y4, @y5, @yhisto, @xhisto);
while ($minlen < $minmax[1]){
    @y2 = (); @y3 = (); @y4 = (); @y5 = ();
    my $maxlen = $minlen + $grouplen;
    if ($maxlen == $minmax[1]){
        $sql = "SELECT * FROM proc WHERE $col>=$minlen and $col<=$maxlen ORDER BY $col";
    }
    else{
        $sql = "SELECT * FROM proc WHERE $col>=$minlen and $col<$maxlen ORDER BY $col";
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

    print "<div>";
    	print "Размер вариации R = $r<br>";
    	print "Среднее линейное отклонение a = $a<br>";
    	print "Дисперсия D = $d<br>";
    	print "Среднее квадратическое отклонение si = $si<br>";
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

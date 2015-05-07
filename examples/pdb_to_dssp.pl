=begin
This example client takes a PDB file, sends it to the REST service that
creates the DSSP data, which is written to a DSSP file.

Example:

    perl pdb_to_dssp.pl 1crn.pdb 1crn.dssp
=cut


use strict;
use warnings;
use HTTP::Request::Common;
use LWP::UserAgent;
use JSON qw( decode_json );


my $url_xssp = "http://www.cmbi.umcn.nl/xssp/";
my $ua = LWP::UserAgent->new;
my $input = shift;
my $output = shift;


die "Usage: pdb_to_dssp.pl <infile> <outfile>\n" unless -f $input and \
  defined $output;


# Sends a request to the server to create a dssp file from the pdb file data.
# If an error occurs the program exits.
my $url_create = $url_xssp . "api/create/pdb_file/dssp/";
my $response = $ua->request(POST $url_create,
  Content_Type => "multipart/form-data",
  Content => [
    file_ => [$input],
  ]);
die $response->status_line unless $response->is_success;


# If the request is successful, the id of the job running on the server is
# returned.
my $content = decode_json($response->content);
my $id = $content->{'id'};


# Loops unil the job running on the server has finished, either successfully
# or due to an error.
my $ready = 0;
until ($ready) {
  # Check the status of the running job.
  # If an error occurs the program exits.
  my $url_status = $url_xssp . "api/status/pdb_file/dssp/" . $id . "/";
  $response = $ua->request(GET $url_status);
  die $response->status_line unless $response->is_success;

  # If the request is successful, the status is returned.
  my $content = decode_json($response->content);
  my $status = $content->{'status'};
  print "Job status is: " . $status . "\n";

  if ($status eq 'SUCCESS') {
    $ready = 1;
  } elsif ($status eq 'FAILURE' or $status eq 'REVOKED') {
    die $status;
  } else {
    sleep 5;
  }
}


# Requests the result of the job. If an error occurs the program exits.
my $url_result = $url_xssp . "api/result/pdb_file/dssp/" . $id . "/";
$response = $ua->request(GET $url_result);
die $response->status_line unless $response->is_success;

$content = decode_json($response->content);
my $result = $content->{'result'};
open(my $g, ">$output") or die "Could not open output file: $!\n";
print $g $result;
close($g);

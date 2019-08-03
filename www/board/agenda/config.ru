require 'whimsy/asf/rack'

require File.expand_path('../main.rb', __FILE__)

# https://svn.apache.org/repos/infra/infrastructure/trunk/projects/whimsy/asf/rack.rb
use ASF::Auth::MembersAndOfficers do |env|
  # allow access to bootstrap related content
  if 
    env['PATH_INFO'] =~ %r{^/(app|sw)\.js(\.map)?$} or
    env['PATH_INFO'] =~ %r{\.js\.rb?$} or
    env['PATH_INFO'] =~ %r{^/stylesheets/.*\.css\$} or
    env['PATH_INFO'] =~ %r{^/[-\d]+/bootstrap.html$} or
    env['PATH_INFO'] == '/manifest.json'
  then
    next true
  end

  # allow access to historical-comments and post for reporter tool.
  # notes:
  # - historical-comments is filtered by routes.rb to only include the list of
  #   PMCs that the user is a member of for non-ASF-members and non-officers.
  # - post is limited to ASF members, officers, and members of the PMC whose
  #   report is being posted.
  next true if env['PATH_INFO'] == '/json/historical-comments'
  next true if env['PATH_INFO'] == '/json/post'

  # additionally authorize all invited guests
  agenda = dir('board_agenda_*.txt').sort.last
  if agenda
    Agenda.parse(agenda, :full)
    roll = Agenda[agenda][:parsed].find {|item| item['title'] == 'Roll Call'}
    roll['people'].keys.include? env['REMOTE_USER']
  end
end

use ASF::HTTPS_workarounds

use ASF::ETAG_Deflator_workaround

use ASF::DocumentRoot

run Sinatra::Application

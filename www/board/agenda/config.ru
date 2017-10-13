require 'whimsy/asf/rack'

require File.expand_path('../main.rb', __FILE__)

# https://svn.apache.org/repos/infra/infrastructure/trunk/projects/whimsy/asf/rack.rb
use ASF::Auth::MembersAndOfficers do |env|
  # allow access to bootstrap related content
  if 
    %w(/app.js /sw.js /stylesheets/app.css).include? env['PATH_INFO'] or
    env['PATH_INFO'] =~ %r{^/[-\d]+/bootstrap.html$}
  then
    next true
  end

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

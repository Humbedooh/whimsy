#!/usr/bin/ruby1.9.1
$LOAD_PATH.unshift File.realpath(File.expand_path('../../../lib', __FILE__))

require 'mail'
require 'wunderbar'
require 'whimsy/asf'

# link to members private-arch
MBOX = 'https://mail-search.apache.org/members/private-arch/members/'

# link to roster page
ROSTER = 'https://whimsy.apache.org/roster/committer'

# get a list of current members messages
year = Time.new.year.to_s
archive = Dir["/srv/mail/members/#{year}*/*"]

# select messages that have a subject line starting with [MEMBER NOMINATION]
emails = []
archive.each do |email|
  next if email.end_with? '/index'
  message = IO.read(email, mode: 'rb')
  next unless message[/^Date: .*/].to_s.include? year
  subject = message[/^Subject: .*/]
  next unless subject.include? "[MEMBER NOMINATION]"
  mail = Mail.new(message)
  emails << mail if mail.subject.start_with? "[MEMBER NOMINATION]"
end

# parse nominations for names and ids
MEETINGS = ASF::SVN['private/foundation/Meetings']
meeting = Dir["#{MEETINGS}/2*"].sort.last
nominations = IO.read("#{meeting}/nominated-members.txt").
  scan(/^-+--\s+(.*?)\n/).flatten

nominations.shift if nominations.first == '<empty line>'
nominations.pop if nominations.last.empty?

nominations.map! do |line| 
  {name: line.gsub(/<.*|\(\w+@.*/, '').strip, id: line[/([.\w]+)@/, 1]}
end

# location of svn repository
svnurl = `cd #{meeting}; svn info`[/URL: (.*)/, 1]

# produce HTML output of reports, highlighting ones that have not (yet)
# been posted
_html do
  _title 'Member nominations cross-check'

  _style %{
    .missing {background-color: yellow}
  }

  # common banner
  _a href: 'https://whimsy.apache.org/' do
    _img title: "ASF Logo", alt: "ASF Logo",
      src: "https://www.apache.org/img/asf_logo.png"
  end

  _h1_! do
    _ "Nominations in "
    _a 'svn', href: File.join(svnurl, 'nominated-members.txt')
  end

  _ul nominations.sort_by {|person| person[:name]} do |person|
    _li! do
      _a person[:name], href: "#{ROSTER}/#{person[:id]}"
    end
  end

  nominations.map! {|person| person[:name].downcase}

  _h1_.posted! "Posted nominations reports"

  # attempt to sort reports by PMC name
  emails.sort_by! do |mail| 
    mail.subject.downcase.gsub('- ', '')
  end

  # output an unordered list of subjects linked to the message archive
  _ul emails do |mail|
    _li do
      href = MBOX + mail.date.strftime('%Y%m') + '.mbox/' + 
        URI.escape('<' + mail.message_id + '>')

      if nominations.any? {|name| mail.subject.downcase =~ /\b#{name}\b/}
        _a.present mail.subject, href: href
      else
        _a.missing mail.subject, href: href
      end
    end
  end
end

# produce JSON output of reports
_json do
  _ reports do |mail|
    _subject mail.subject
    _link MBOX + URI.escape('<' + mail.message_id + '>')
    _missing missing.any? {|title| mail.subject.downcase =~ /\b#{title}\b/}
  end
end

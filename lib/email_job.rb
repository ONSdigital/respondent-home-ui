require 'notifications/client'

# Sucker Punch job class for sending email in the background using GOV.UK Notify.
class EmailJob
  include SuckerPunch::Job

  def perform(email_address, contact_data, template, api_key)
    client = Notifications::Client.new(api_key)
    notification = client.send_email(to: email_address, template: template,
                                     personalisation: contact_data)
    logger.info "Sent email with notification ID '#{notification.id}'"
  rescue Notifications::Client::RequestError => e
    logger.error "Failed to send email: (#{e.code}) '#{e.message}'"
  end
end

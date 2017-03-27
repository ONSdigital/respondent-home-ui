require 'aws-sdk'

require_relative 'contact_data'

# Sucker Punch job class for storing contact details in the background using
# Amazon S3.
class S3Job
  include SuckerPunch::Job

  # rubocop:disable Metrics/AbcSize
  def perform(bucket, contact_data)
    s3 = Aws::S3::Resource.new

    # INC0039549: Force the S3 object name to be ASCII so the object creation
    # event always fires.
    object_name = "#{ContactData.new(contact_data).ascii_name}-#{Time.now.utc.to_i}.json"
    object = s3.bucket(bucket).object(object_name)
    object.put(acl: 'authenticated-read',
               body: contact_data.to_json,
               content_type: 'application/json',
               server_side_encryption: 'AES256')
    logger.info 'Stored individual questionnaire request details in S3'
  rescue Aws::S3::Errors::ServiceError => e
    logger.error "Failed to store individual questionnaire request details in S3: (#{e.code}) '#{e.message}'"
  end
  # rubocop:enable Metrics/AbcSize
end

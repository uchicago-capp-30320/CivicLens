### Model/Resource Documentation

Document key entities that your application depends upon.
Should roughly correspond to your database tables and/or REST resources.

For each:

* The name and purpose of attributes, including types, relationships, and other constraints.
* Brief explanations of any key concepts useful to provide context for the data model.
#### Example

(I'd encourage you to be a bit more descriptive where it would be useful for your own app.)

**Photo**

This represents the metadata for a single image upload.
Important to note, the image itself is not stored here, since it can be updated so needs a 1-Many relationship with `PhotoVersion`. {note: this is an important detail, as it might surprise a person learning the system, think about what surprises might exist in your data model}

| Name              | Type                 | Description               |
| ----------------- | -------------------- | ------------------------- |
| user              | ForeignKey(User)     | the creator of this image |
| uploaded_at       | DateTime             | time uploaded (UTC)       |
| moderation_status | ModerationStatusEnum | PUBLIC, HIDDEN, REMOVED   |
| ...               |                      |                           |

**PhotoVersion**

Represents a point-in-time version of a photo.  Metadata is stored on `Photo`, but individual versions are stored here.

The actual raw bytes of the image are uploaded to our cloud provider (AWS S3 currently) and those URLs are associated with photos through this table.

| Name               | Type              | Description                                                  |
| ------------------ | ----------------- | ------------------------------------------------------------ |
| photo              | ForeignKey(Photo) | link to photo metadata                                       |
| version_num        | int               | unique per photo                                             |
| remote_storage_url | url               | Link to specific image version in  object storage (e.g. S3). |
| note               | TEXT              | note associated with this image version                      |
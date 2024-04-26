from django.db import models


class Dockets(models.Model):
    "Model representing a docket."
    id = models.CharField(max_length=255, primary_key=True)
    docketType = models.CharField(max_length=255, blank=True)
    lastModifiedDate = models.DateTimeField()
    agencyId = models.CharField(max_length=100, blank=True)
    title = models.TextField()
    objectId = models.CharField(max_length=255, blank=True)
    highlightedContent = models.CharField(max_length=255, blank=True)


class Documents(models.Model):
    "Model representing a document."
    id = models.CharField(max_length=255, primary_key=True)
    documentType = models.CharField(max_length=255, blank=True)
    lastModifiedDate = models.DateTimeField()
    frDocNum = models.CharField(max_length=100, blank=True)
    withdrawn = models.BooleanField(default=False)
    agencyId = models.CharField(max_length=100, blank=True)
    commentEndDate = models.DateField(null=True, blank=True)
    postedDate = models.DateField()
    title = models.TextField()
    docket = models.ForeignKey(Dockets, on_delete=models.CASCADE)
    subtype = models.CharField(max_length=255, blank=True)
    commentStartDate = models.DateField(null=True, blank=True)
    openForComment = models.BooleanField(default=False)
    objectId = models.CharField(max_length=100, blank=True)
    fullTextXmlUrl = models.CharField(max_length=255, blank=True)
    subAgy = models.CharField(max_length=255, blank=True)
    agencyType = models.CharField(max_length=100, blank=True)
    CFR = models.CharField(max_length=100, blank=True)
    RIN = models.CharField(max_length=100, blank=True)
    title = models.CharField(max_length=255)
    summary = models.TextField()
    dates = models.CharField(max_length=255, blank=True)
    furtherInformation = models.TextField(blank=True)
    supplementaryInformation = models.TextField(blank=True)


class PublicComments(models.Model):
    "Model representing a public comment."
    id = models.CharField(max_length=255, primary_key=True)
    objectId = models.CharField(max_length=255)
    commentOn = models.CharField(max_length=255, blank=True)
    document = models.ForeignKey(Documents, on_delete=models.CASCADE)
    duplicateComments = models.IntegerField(default=0)
    stateProvinceRegion = models.CharField(max_length=100, blank=True)
    subtype = models.CharField(max_length=100, blank=True)
    comment = models.TextField()
    firstName = models.CharField(max_length=255, blank=True)
    lastName = models.CharField(max_length=255, blank=True)
    address1 = models.CharField(max_length=200, blank=True)
    address2 = models.CharField(max_length=200, blank=True)
    city = models.CharField(max_length=100, blank=True)
    category = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)
    email = models.EmailField(max_length=100, blank=True)
    phone = models.CharField(max_length=50, blank=True)
    govAgency = models.CharField(max_length=100, blank=True)
    govAgencyType = models.CharField(max_length=100, blank=True)
    organization = models.CharField(max_length=255, blank=True)
    originalDocumentId = models.CharField(max_length=100, blank=True)
    modifyDate = models.DateTimeField()
    pageCount = models.IntegerField()
    postedDate = models.DateField()
    receiveDate = models.DateField()
    title = models.TextField()
    trackingNbr = models.CharField(max_length=255, blank=True)
    withdrawn = models.BooleanField(default=False)
    reasonWithdrawn = models.CharField(max_length=255, blank=True)
    zip = models.CharField(max_length=50, blank=True)
    restrictReason = models.CharField(max_length=100, blank=True)
    restrictReasonType = models.CharField(max_length=100, blank=True)
    submitterRep = models.CharField(max_length=100, blank=True)
    submitterRepAddress = models.CharField(max_length=255, blank=True)
    submitterRepCityState = models.CharField(max_length=100, blank=True)

class Search(models.Model):
    searchterm = models.CharField(max_length=100)
    
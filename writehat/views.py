# May Odyn smile on your Chain and Thorim empower your Chomp

import re
import json
import base64
import logging
import uuid as uuidlib
from datetime import datetime

# django
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.html import escape
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.views.decorators.http import require_http_methods
from django.utils.datastructures import MultiValueDictKeyError
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.views.decorators.clickjacking import xframe_options_exempt
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.contrib import messages


# WRITEHAT

from writehat import validation

from writehat.lib.util import *
from writehat.lib.dread import *
from writehat.lib.errors import *
from writehat.lib.figure import *
from writehat.lib.report import *
from writehat.lib.finding import *
from writehat.lib.resolve import *
from writehat.lib.customer import *
from writehat.lib.dbImport import *
from writehat.lib.dbExport import *
from writehat.lib.revision import *
from writehat.lib.engagement import *
from writehat.lib.findingForm import *
from writehat.components.base import *
from writehat.lib.findingGroup import *
from writehat.lib.pageTemplate import *
from writehat.lib.findingCategory import *
from writehat.lib.engagementFinding import *
from writehat.lib.excel import generateExcel




log = logging.getLogger(__name__)

####RENDERING VIEWS####

# WIP homepage
@login_required
def home(request):

    return render(request,"pages/home.html", {})



# Just a redirect to home
def index(request):

    return HttpResponseRedirect('/engagements')


# Validation - returns allowed characters
@require_http_methods(['GET'])
@csrf_exempt
def validationWhitelists(request):

    return JsonResponse({
        'names': list(validation.allowed_for_names),
        'strict_names': list(validation.allowed_for_strict_names),
    })


# Returns CVSS details
@require_http_methods(['POST'])
@csrf_exempt
def validationCVSS(request):

    post_data = request.POST.dict()
    cvss_data = CVSS.fromDict(post_data)

    return JsonResponse({
        'vector': cvss_data.vector,
        'severity': cvss_data.severity,
        'score': cvss_data.score,
    })

def intOrFail(maybeInt):
    try:
        x = int(maybeInt)
    except ValueError:
        raise DreadValidationError('cannot convert value to integer')
    if x > 10:
        raise DreadValidationError('value is out of valid range')
    return x
 
# Returns DREAD details 
# There is probably a more efficient way to do this
@require_http_methods(['POST'])
@csrf_exempt
def validationDREAD(request):
    d = {}
    # a bit ugly in exchange for maximum security
    #try:
    d['dreadDamage'] = intOrFail(request.POST['dreadDamage'])
    d['dreadReproducibility'] = intOrFail(request.POST['dreadReproducibility'])
    d['dreadExploitability'] = intOrFail(request.POST['dreadExploitability'])
    d['dreadAffectedUsers'] = intOrFail(request.POST['dreadAffectedUsers'])
    d['dreadDiscoverability'] = intOrFail(request.POST['dreadDiscoverability'])
#except MultiValueDictKeyError:
    #    raise DreadValidationError('missing required parameter')

    # validate input and assign to dict
    dread = DREAD(DREAD.createVector(d))


    return JsonResponse({
        'severity': dread.severity,
        'score': dread.score,
    })




# Given a reportID, get the JSON object containing the list of associated components
@require_http_methods(['GET'])
@csrf_protect
def reportEdit(request,uuid):
    log.debug("reportEdit() called; UUID: {0}".format(uuid))
    log.debug("Found {0} available components".format(len(settings.VALID_COMPONENTS)))

    report = Report.get(id=uuid)
    report.populateForm()

    return render(request,"pages/reportEdit.html", \
        {
            "report": report,
            "engagement": report.engagement,
            "componentsList": settings.VALID_COMPONENTS,

        })

@require_http_methods(['GET'])
def reportRevisions(request, uuid):
    log.debug("reportRevisions() called; UUID: {0}".format(uuid))
    log.debug("Found {0} available components".format(len(settings.VALID_COMPONENTS)))

    report = Report.get(id=uuid)

    return render(request, "pages/reportRevisions.html", {
        "report": report,
        "engagement": report.engagement,
        "revisions": report.revisions
    })

@require_http_methods(['GET'])
@csrf_protect
def componentReviewStatus(request,uuid):
    log.debug("componentReviewStatus() called; UUID: {0}".format(uuid))
    log.debug("Found {0} available components".format(len(settings.VALID_COMPONENTS)))

    report = Report.get(id=uuid)

    try:
        engagement = Engagement.get(id=report.engagementParent)
    except (AttributeError, Engagement.DoesNotExist):
        engagement = ''

    return render(request,"pages/componentReviewStatus.html", \
        {
            "report": report,
            "engagement": engagement,
            "componentsList": settings.VALID_COMPONENTS,
            "currentUser": { "id": request.user.id, "name": f"{request.user.first_name} {request.user.last_name}" },
        })


# Renders the component editing form
@csrf_protect
@require_http_methods(['GET'])
def componentEdit(request,uuid,form=None):

    log.debug("componentEdit() called; UUID: {0}".format(uuid))
    #try:
    component = BaseComponent.get(uuid)
    #except:
    #return HttpResponse('Security Violation!')

    return render(request,"pages/componentEdit.html", {"component": component})



# The handler for saving incoming report component data
@csrf_protect
@require_http_methods(['POST'])
def componentSave(request,uuid):

    log.debug("componentSave() called; UUID: {0}".format(uuid))
    log.debug("Form data: {0}".format(request.POST))

    try:
        component = BaseComponent.get(uuid)
        log.debug("BaseComponent.get instantiated")

        component.updateFromForm(request.POST)
        log.debug("Form data applied to component")

        component.save()
        log.debug("Component saved")

        message = "Sucessfully Saved!"
        log.debug("Rendering response")
        return render(request,"pages/componentEdit.html", {"component": component})

    except ComponentFormError:
        response = HttpResponse('Invalid Form')
        response.status_code = 400
        return response  

    except ComponentError: 
        response = HttpResponse('Invalid Component')
        response.status_code = 500
        return response

# The handler for updating a component's status field
@csrf_protect
@require_http_methods(['POST'])
def componentStatusUpdate(request,uuid):
    log.debug("componentStatusUpdate() called; UUID: {0}".format(uuid))
    log.debug("Form data: {0}".format(request.body))

    try:
        component = BaseComponent.get(uuid)
        log.debug("BaseComponent.get instantiated")

        component.updateFromForm(json.loads(request.body), selective=True)
        log.debug("Form data applied to component")

        component.save()
        log.debug("Component saved")

        message = "Sucessfully Saved!"
        return JsonResponse({"component": uuid, "status": component.reviewStatus}, safe=False)

    except ComponentFormError:
        response = HttpResponse('Invalid Form')
        response.status_code = 400
        return response  

    except ComponentError: 
        response = HttpResponse('Invalid Component')
        response.status_code = 500
        return response

# The handler to process incoming POST requests creating new reports
@csrf_protect
@require_http_methods(['POST'])
def reportCreate(request, uuid=None, fromTemplate=False):


    log.debug(f"reportCreate with engagementParent uuid: {uuid}")

    jsondata = request.body
    if not validation.isValidJSON(jsondata):
        response = HttpResponse('Invalid Data!')
        log.warning("Invalid JSON data in request body")
        log.debug(f"  jsondata: {jsondata}")
        response.status_code = 400
        return response
    decodedJson = json.loads(jsondata)

    # Validate that required keys are present in JSON
    if not all([k in decodedJson for k in \
        ['name', 'reportComponents']]):
        response = HttpResponse('Invalid Data!')
        response.status_code = 400
        return response

    try:
        reportName = decodedJson['name']
        log.debug(f"reportName: {reportName}")
        reportComponents = decodedJson['reportComponents']
        status = decodedJson.get('status')
        # Everything is validated, lets instantiate the report
        report = None
        if uuid:
            log.debug(f"saving report (with engagementParent) reportComponents: {reportComponents}")
            report = Report.new(name=reportName, components=reportComponents, engagementParent=uuid, status=status)
        #    report.engagementParent = uuid
       #     report.save()
        else:
            if fromTemplate:
                report = SavedReport.new(name=reportName, components=reportComponents, status=status)
            else:
                report = Report.new(name=reportName, components=reportComponents, status=status)

    except ReportValidationError:
        log.warn("reportCreate() threw ReportValidationError")
        response = HttpResponse('Invalid Data!')
        response.status_code = 400
        return response

    log.debug(f"Returning HttpResponse; report.id: {report.id}")
    response = HttpResponse(report.id)
    response.status_code = 200
    return response



# Loads the page where a user can select the components they want in their new reports
@csrf_protect
@require_http_methods(['GET'])
def reportNew(request, uuid):

    componentList = settings.VALID_COMPONENTS
    engagement = Engagement.get(id=uuid)
    log.debug(f'Detected components: {componentList}')

    return render(request,"pages/reportNew.html", {
        "componentsList": componentList,
        "engagement": engagement,
        "report": BaseReport
    })



# Deletes the report with the specified UUID
@csrf_protect
@require_http_methods(['GET','POST'])
def reportDelete(request, uuid, fromTemplate=False):


    if fromTemplate:
        try:
            report = SavedReport.objects.get(id=uuid)
            returnUrl = ""
        except SavedReport.DoesNotExist:
            log.debug(f'No savedReport found with ID {uuid}')
            response.status_code = 400
    else:
        try:
            report = Report.objects.get(id=uuid)
        except Report.DoesNotExist:
            log.debug(f'No report found with ID {uuid}')
            response.status_code = 400
    name = escape(report.name)
    report.delete()
    response = HttpResponse(f'Successfully deleted report "{name}"')
    response.status_code = 200
    return response


@csrf_protect
@require_http_methods(['GET','POST'])
def templateDelete(request,uuid):
    return reportDelete(request,uuid,fromTemplate=True)


@csrf_protect
@require_http_methods(['POST'])
def templateUpdate(request,uuid):
    return reportUpdate(request,uuid,fromTemplate=True)


@csrf_protect
@require_http_methods(['POST'])
def reportUpdate(request,uuid,fromTemplate=False):

    try:
        # Get the JSON from the HTTP POST
        reportJSON = json.loads(request.body)

        componentJSON = reportJSON.get('reportComponents', None)
        reportName = reportJSON.get('name', None)
        reportPageTemplate = reportJSON.get('pageTemplateID', None)
        reportFindings = reportJSON.get('reportFindings', None)
        reportStatus = reportJSON.get('status', None)

        if componentJSON is not None:
            log.debug("In reportUpdate()")
            log.debug(f"name: {reportName}")
            log.debug("componentJSON:")
            [ log.debug("  {0}".format(k)) for k in componentJSON ]

        # Instantiate a Report object
        if fromTemplate:
            log.debug("fromTemplate is true:")
            report = SavedReport.get(id=uuid)
            report.update(componentJSON, reportName, reportPageTemplate, status=reportStatus)
        else:
            log.debug("fromTemplate is false:")
            # Update the report
            report = Report.get(id=uuid)
            report.update(componentJSON, reportName, reportPageTemplate, reportFindings, status=reportStatus)


    except ReportValidationError as e:
        if len(str(e)) == 0:
            e = "UNDEFINED"
        error_msg = f"Component Validation Error ({e})"
        log.error(error_msg)
        response = HttpResponse(escape(error_msg), content_type='text/html')
        response.status_code = 400
        return response

    # Add to the list for new components to create
    # Send back the same JSON object but with missing UUIDS for the new components
    components = json.loads(report._components)
    return JsonResponse(components, safe=False)



# Displays the list of existing reports and allows for the creation of a new one
@require_http_methods(['GET'])
def reportsHome(request):

    reports = []
    for r in Report.objects.all():
        # since we're sorting by modifiedDate
        # we need to make sure it exists, otherwise things break
        if r.modifiedDate:
            report = Report.get(id=r.id)
            reports.append(report)

    return render(request,"pages/reports.html", {'reports':reports})


def getReport(reportId):

    try:
        report = Report.get(id=reportId)
    except Report.DoesNotExist:
        report = SavedReport.get(id=reportId)

    return report


def getFinding(findingId):
    '''
    Given a finding UUID, retrieve the finding
    regardless of scoringType or whether it's an 
    EngagementFinding or DatabaseFinding
    '''

    finding = None

    for findingType in (
        EngagementFinding,
        BaseDatabaseFinding
    ):
        try:
            finding = findingType.get_child(id=findingId)
            break
        except FindingError:
            continue

    return finding


def getEngagement(engagementId):

    try:
        engagement = Engagement.get(id=engagementId)
    except Engagement.DoesNotExist:
        engagement = None
    return engagement



# returns a list of finding GUIDs for a report
@csrf_exempt
@require_http_methods(['POST'])
def getReportFindings(request):

    engagementID = request.POST.get('engagementID', None)
    reportID = request.POST.get('reportID', None)

    if engagementID and reportID:
        report = Report.get(id=reportID, engagementParent=engagementID)
        return JsonResponse([str(f.id) for f in report.findings], safe=False)

    else:
        response = HttpResponse('Missing parameters: must have "engagementID" and "reportID"')
        response.status_code = 400
        return response


# returns a list of finding GUIDs for a report
@csrf_exempt
@require_http_methods(['GET'])
def getReportComponents(request, uuid):

    report = getReport(uuid)
    return JsonResponse([{'id': c.id, 'name': c.name} for c in report.components], safe=False)


# Renders the requested pane in panes/*.html
@csrf_protect 
@require_http_methods(['POST'])
def renderPane(request, pane):

    itemIDs = json.loads(request.body)

    # sanitize pane parameter to prevent LFI
    bad_chars = str.maketrans(dict.fromkeys('./'))
    pane = pane.translate(bad_chars)

    # reports
    try:
        report = getReport(itemIDs['reportID'])
        report.populateForm()
    except KeyError:
        report = ''
    # components
    try:
        component = BaseComponent.get(itemIDs['componentID'])
    except KeyError:
        component = ''
    # findings
    try:
        finding = getFinding(itemIDs['findingID'])
    except KeyError:
        finding = ''

    try:
        engagement = getEngagement(itemIDs['engagementID'])
    except KeyError:
        engagement = ''

    response = render(request,'panes/{}.html'.format(pane), \
        {
            'report': report,
            'finding': finding,
            'component': component,
            'componentsList': settings.VALID_COMPONENTS,
            'findingsTree': (getFindingsTree('findings') if pane == 'categoryBrowse' else '')
        })

    return response



# Renders the requested modal in modals/*.html
@csrf_protect 
@require_http_methods(['POST'])
def renderModal(request, modal):

    itemIDs = json.loads(request.body)

    # sanitize modal parameter to prevent LFI
    bad_chars = str.maketrans(dict.fromkeys('./'))
    modal = modal.translate(bad_chars)

    # report
    try:
        try:
            report = Report.get(id=itemIDs['reportID'])
        except Report.DoesNotExist:
            report = SavedReport.get(id=itemIDs['reportID'])
    except KeyError:
        report = ''
    try:
        component = BaseComponent.get(itemIDs['componentID'])
        if not report:
            report = component.getReportParent
    except KeyError:
        component = ''

    # engagement
    engagement = itemIDs.get('engagementID', '')
    if engagement:
        engagement = Engagement.get(id=engagement)

    # findingGroup
    findingImportForm = None
    fgroupID = itemIDs.get('fgroupID', '').strip()

    if fgroupID:
        fgroup = BaseFindingGroup.get_child(id=itemIDs['fgroupID'])
        fgroup.populateForm(formClass=EditFgroupForm)
        editFgroupForm = fgroup.form
        if modal == 'findingDatabaseSelect':
            findingImportForm = FindingImportForm(scoringType=fgroup.scoringType)
    else:
        fgroup = ''
        editFgroupForm = EditFgroupForm

    response = render(request, f'modals/{modal}.html', \
        {
            'modalName': modal,
            'engagement': engagement,
            'report': report,
            'component': component,
            'componentsList': settings.VALID_COMPONENTS,
            'findingImportForm': findingImportForm,
            'NewFgroupForm': NewFgroupForm,
            'EditFgroupForm': editFgroupForm,
            'savedReportImportForm': SavedReportImportForm,
            'categoryAddForm': CategoryAddForm,
            'customerForm': CustomerForm(auto_id=CustomerForm.auto_id_str),
            'categoryEditForm': CategoryAddForm(auto_id='id_edit_%s')
        })

    return response



@csrf_protect
@require_http_methods(['POST'])
# GET the report ID from the URL
def reportClone(request,uuid):
    
    try:
        report = Report.get(id=uuid)
    except Report.DoesNotExist:
        report = SavedReport.get(id=uuid)

    clonedReport = report.clone(templatableOnly=False)
    return HttpResponse(clonedReport.id)



# Generate the HTML for the report
@csrf_protect
@xframe_options_exempt
@require_http_methods(['POST', 'GET'])
# GET the report ID from the URL
def reportGenerate(request,uuid):
    '''
    Render/preview a Report, SavedReport, or Component
    '''

    try:
        # TODO: Make 'page-break' div between sections optional (perhaps by
        # adding 'break-before' to BaseComponent?)

        try:
            report = Report.get(id=uuid)
        except Report.DoesNotExist:
            report = SavedReport.get(id=uuid)

        return HttpResponse(report.render(), content_type='text/html; charset=utf-8')

    except SavedReport.DoesNotExist:
        log.debug("UUID did not match any reports; trying components")

        # Render a single component
        component = BaseComponent.get(uuid)
        # remove the page break since we're just previewing
        component.pageBreakBefore = False

        # Instantiate the component's report, then remove all other components
        try:
            report = Report.get(id=component.reportParent)
        except Report.DoesNotExist:
            report = SavedReport.get(id=component.reportParent)
        components = [component]
        report.components = components
        response = HttpResponse(report.render(), content_type='text/html; charset=utf-8')
        return response 


# load the new database finding form with the cvss form
def findingCvssNew(request):
    log.debug("Called findingCvssNew")
    form = CVSSDatabaseFindingForm
    return render(request,"pages/findingNew.html",{"form":form,"scoringType":"CVSS"})

# load the new database finding form with the dread form
def findingDreadNew(request):
    log.debug("Called findingDreadNew")
    form = DREADDatabaseFindingForm
    return render(request,"pages/findingNew.html",{"form":form,"scoringType":"DREAD"})


# load the new database finding form with the dread form
def findingProactiveNew(request):
    log.debug("Called findingProactiveNew")
    form = ProactiveDatabaseFindingForm
    return render(request,"pages/findingNew.html",{"form":form,"scoringType":"PROACTIVE"})


# Edit an existing "findings database" entry. Should be very similiar to findingsView, except with all the editing tools loaded.
@csrf_protect
@require_http_methods(['POST', 'GET'])
def findingEdit(request,uuid):

    finding = BaseDatabaseFinding.get_child(id=uuid)
    if request.method == 'GET':
        # instantiate a cvssFinding object by passing in an instance of the model
        finding.populateForm()
        #log.info(cvssFinding.form.data)
        #log.info(str(cvssFinding.form['categoryID']))
        return render(request,"pages/findingEdit.html",{'finding': finding})

    elif request.method == 'POST':
        finding.updateFromPostData(request.POST)
        log.debug(f'views.py finding edit save...')
        finding.save()
        return HttpResponse(finding.id)


@csrf_protect
@require_http_methods(['POST'])
def findingDelete(request,uuid):

    try:
        databaseFinding = BaseDatabaseFinding.get_child(id=uuid)
        databaseFinding.delete()
        return HttpResponse(databaseFinding.id)

    except FindingError:
        log.debug(f'No finding found with ID {uuid}')
        response.status_code = 400
        return response


# This is where NEW findings requests are send via POST. Existing findings will get sent to findingEdit as a post. 
@csrf_protect
@require_http_methods(['POST'])
def findingCreate(request):

    # we need to know the form type, its passed in via a hidden form field
    if 'scoringType' in request.POST:
        scoringType = request.POST['scoringType']
    else:
        raise FindingCreateError("Missing 'scoringType' parameter")
    # for security, check the value or form type. Anything other than CVSSForm or DREADForm creates and error        
    if scoringType == 'CVSS':
        finding = CVSSDatabaseFinding.new(request.POST)
    elif scoringType == 'DREAD':
        finding = DREADDatabaseFinding.new(request.POST)
    elif scoringType == 'PROACTIVE':
        finding = ProactiveDatabaseFinding.new(request.POST)
    else:
        raise FindingCreateError("Invalid 'scoringType' parameter")
       
    finding.save()
    log.debug(f'Created new DatabaseFinding, UUID: {finding.id}')
    # Return the ID to be handled by javascript on the findingNew page
    # return HttpResponse(finding.id)
    return HttpResponse(finding.id)


# make way to RETRIEVE the details individual per image
@csrf_protect
@require_http_methods(['POST'])
def findingFigureEdit(request, uuid):
    '''
    Updates a finding's list of figures
    '''
    
    findingParent = uuid
    successfulUpdateCount = 0
       
    try: 
        parsedJSON = json.loads(request.body)
    except json.JSONDecodeError:
        raise ImagesUploadError("JSON parsing of image attributes failed")

    # get finding's current list of figures
    old_figures = []
    try:
        for figure in ImageModel.objects.filter(findingParent=findingParent):
            old_figures.append(figure)
    except ImageModel.DoesNotExist:
        pass

    # make sure finding is valid
    try:
        EngagementFinding.get_child(id=uuid)
        log.debug(f"findingFigureEdit called with findingParent {findingParent}")
    except FindingError:
        log.debug(f"findingFigureEdit aborted - finding ID invalid")
        raise ImagesUploadError(f'findingParent "{findingParent}" does not exist')


    # create / update / save new / existing figures
    for order, figure in enumerate(parsedJSON):
        if 'guid' in figure:
            try:
                imageModel = ImageModel.get(id=figure['guid'])
            except ImageModel.DoesNotExist:
                log.debug(f"findingFigureEdit called with missing figureID, tried: {figure['guid']}")
                continue
            if 'size' in figure:
                imageModel.size = figure['size']
            if 'caption' in figure:
                imageModel.caption = figure['caption']
            imageModel.order = order
            imageModel.findingParent = findingParent
            try:
                imageModel.save()
                successfulUpdateCount += 1
                log.debug(f"findingFigureEdit called; successfully saved imageModel {imageModel.id}, with parentID: {findingParent}")
            except:
                log.debug(f"findingFigureEdit failed to save for imageModel {imageModel.id}, with parentID: {findingParent}")

        else:
            log.debug(f"findingFigureEdit called with missing figureID")

    # handle deleted figures - this helps prevent orphans in the database
    new_figures = [f['guid'] for f in parsedJSON]
    for figure in old_figures:
        if str(figure.id) not in new_figures:
            log.debug(f'Deleting figure {figure.id}')
            figure.delete()

    return HttpResponse(f"updated {successfulUpdateCount:,} figures")



@csrf_protect
@require_http_methods(['POST'])
def imageUpload(request):

    log.debug(f"imageUpload called")
    
    extensionToContentType = {'png':'image/png',
                              'jpg':'image/jpeg',
                              'jpeg':'image/jpeg',}

    # check if a file is present
    if request.FILES['file']:
    
        imageModel = ImageModel()
        uploadedFile = request.FILES['file']
        
        
        # retreive and validate the content type of the image (based on the extension)
        extension = uploadedFile.name.split(".")[1].lower()
        contentType = str(extensionToContentType.get(extension ,"error"))
        log.debug(f"Image uploaded with content-type {contentType}")
        imageModel.contentType = contentType
        log.debug(f"imageUpload called with content-type {contentType}")
        if contentType == "error": 
            raise ImagesUploadError("Invalid file extension for uploaded image")
        
        imageModel.data = uploadedFile.read()
        if 'findingParent' in request.POST:
            findingParent = request.POST["findingParent"]
            try:
                CVSSEngagementFinding.get(id=findingParent)
                log.debug(f"imageUpload called with findingParent {findingParent}")
            except CVSSEngagementFinding.DoesNotExist:
                log.debug(f"imageUpload aborted - finding ID invalid")
                raise ImagesUploadError(f'findingParent "{findingParent}" does not exist')
            imageModel.findingParent = request.POST["findingParent"]
            if 'order' in request.POST:
                imageModel.order = request.POST['order']
            else:
                raise ImagesUploadError("Files attached to findings must specifiy order")
        else:
             log.debug(f"imageUpload called with no findingParent")

        if 'caption' in request.POST:
            imageModel.caption = request.POST["caption"]
        if 'size' in request.POST:
            imageModel.size = request.POST["size"]


        imageModel.save()
        log.debug(f"imageUpload successfully saved with resulting ID: {imageModel.id}")
        return HttpResponse(imageModel.id)

    else:
        raise ImagesUploadError("File data not present")


# render the image
@require_http_methods(['GET'])
def imageLoad(request,uuid):
    try:
        imageModel = ImageModel.objects.get(id=uuid)
    except ImageModel.DoesNotExist:
        log.debug(f"imageLoad called with invalid uuid, tried: {uuid}")
        raise ImagesUploadError("Image with specified ID not found")
    log.debug(f"image successfully loaded with ID: {imageModel.id}")
    return HttpResponse(imageModel.data, content_type=imageModel.contentType)


@require_http_methods(['GET'])
def imageMeta(request,uuid):
    try:
        imageModel = ImageModel.get(id=uuid)
    except ImageModel.DoesNotExist:
        log.debug(f"imageMeta called with invalid uuid, tried: {uuid}")
        raise ImagesUploadError("Image with specified ID not found")
    log.debug(f"image metadata successfully loaded with ID: {imageModel.id}")
    imageModelDict = {}
    if imageModel.findingParent:
        imageModelDict['findingParent'] = str(imageModel.findingParent)
    if imageModel.caption:
        imageModelDict['caption'] = imageModel.caption
    if imageModel.size:
        imageModelDict['size'] = imageModel.size
    if imageModel.order:
        imageModelDict['order'] = imageModel.order
    return JsonResponse(imageModelDict)



# Displays the list of existing findings and allows for the creation of a new one
@csrf_protect 
@require_http_methods(['GET', 'POST'])
def findingsList(request):

    findingsTree = getFindingsTree('findings')

    if request.method == 'GET':

        return render(request,"pages/findings.html",{'findingsTree':findingsTree})
        #  findingsList = '{"Web Application":{"Authentication":{"6367f5d6-ee87-42b8-b8d7-3f362330b863":"Authentication Bypass"}},"System Security": {"6367f5d6-ee87-42b8-b8d7-3f362330b863": "LLMNR Enabled"},}'

    elif request.method == 'POST':
        return JsonResponse(findingsTree)





# add a new category to the tree. UUID is for the existing parent item in the tree
@csrf_protect
@require_http_methods(['POST'])
def findingCategoryAdd(request):

    # ensure that the POST parameter categoryName is present
    try:
        categoryName = request.POST["categoryName"]
        try:
            parentUUID = request.POST["categoryParent"]
        except KeyError:
            parentUUID = None
    except MultiValueDictKeyError:
        raise CategoryValidationError("Required parameters for category creation not present in POST data")

    # if categoryParent is blank, create in root
    if not parentUUID:
        parentCategory = DatabaseFindingCategory.getRootNode()
        log.info(parentCategory)
        parentUUID = parentCategory.id

    # ensure that the POST parameter categoryName has nothing malicious in it
    try:
        validation.isValidName(categoryName)
    except ValidationError:
        response = HttpResponse("Invalid Category Name",status=400)
        return response

    # create the new category
    newCategory = DatabaseFindingCategory(name=categoryName, categoryParent=parentUUID)
    newCategory.save()

    #return the ID of the new category
    return HttpResponse(newCategory.id)



@csrf_protect
@require_http_methods(['POST'])
def findingCategoryEdit(request,uuid):
    try:
        category = DatabaseFindingCategory.objects.get(id=uuid)

    except DatabaseFindingCategory.DoesNotExist:
        raise CategoryError("Cannot locate specified category")

       # ensure that the POST parameter categoryName is present
    try:
        categoryName = request.POST["categoryName"]
        try:
            parentUUID = request.POST["categoryParent"]
            if len(parentUUID) == 0:
                parentUUID = None
        except KeyError:
            parentUUID = None
    except MultiValueDictKeyError:
        raise CategoryValidationError("Required parameters for category creation not present in POST data")  
        
    # ensure that the POST parameter categoryName has nothing malicious in it
    try:
        validation.isValidName(categoryName)
    except ValidationError:
        response = HttpResponse("Invalid Category Name",status=400)
        return response


    # if categoryParent is blank, create in root
    if not parentUUID:
        parentCategory = DatabaseFindingCategory.getRootNode()
        log.info(parentCategory)
        parentUUID = parentCategory.id

    # prevents infinite loops via circular inheratance!
    try:
        validation.isValidParent(uuid,parentUUID)     
    except ValidationError:
        response = HttpResponse("Circular reference detected",status=400)
        return response
   
    category.name = categoryName
    category.categoryParent = parentUUID
    category.save()

    return HttpResponse("Successfully edited category")



# used to remove a category from the tree
@csrf_protect
@require_http_methods(['POST'])
def findingCategoryDelete(request, uuid):
    
    # attempt to load the specified category
    try:
        toDelete = DatabaseFindingCategory.objects.get(id=uuid)

    except DatabaseFindingCategory.DoesNotExist:
        raise CategoryRemoveError("Cannot locate specified category")


    # Check and see if this category has children. If it does, deny the deletion
    categoryChildren = DatabaseFindingCategory.objects.filter(categoryParent=uuid)
    cvssFinding = CVSSDatabaseFinding.objects.filter(categoryID=uuid)
    dreadFinding = DREADDatabaseFinding.objects.filter(categoryID=uuid)
    proactiveFinding = ProactiveDatabaseFinding.objects.filter(categoryID=uuid)

    if categoryChildren.exists():
        response = HttpResponse("Cannot remove categories with child categories", status=400)
        return response

    if cvssFinding.exists() or dreadFinding.exists() or proactiveFinding.exists():
        response = HttpResponse("Cannot remove categories with child findings", status=400)
        return response

    # actually remove the category
    toDelete.delete()

    response = HttpResponse("Successfully deleted category")
    response.status = 200
    return response




# check the last modified timestamp of a model
@csrf_protect 
@require_http_methods(['GET','POST'])
def timestamp(request,uuid):

    hint = request.POST.get('hint', '')
    if hint and not isValidModelHint(hint):
        raise ValidationError("hint value contains invalid characters or is empty")

    p = resolve(uuid,hint)

    return HttpResponse(p.modifiedDate)


@csrf_protect
@require_http_methods(['POST'])
def revisionLoad(request):
    id = request.POST["UUID"]
    version = request.POST["version"]
    fieldName = request.POST["fieldName"]
    log.debug("Views.loadRevision called; UUID: %s (fieldName: %s, version: %s)" % (id,fieldName,version))
    try:
        p = Revision.objects.get(parentId=id,fieldName=fieldName,version=version)
    except Revision.DoesNotExist:
        raise RevisionError("Revision does not exist for this ID/fieldname/version combo")
    return HttpResponse(escape(p.fieldText))


#@require_http_methods(['GET'])
#def revisionsList(request,uuid):
#    log.debug(f"Revision.getVersionList called; uuid: {uuid}")
#    return HttpResponse(escape(Revision.listRevisions(uuid)))


@require_http_methods(['POST'])
def revisionsList(request):
    uuid = request.POST["uuid"]
    isComponent = json.loads(request.POST["isComponent"].lower())
    field = request.POST["field"]
    log.debug(f"Revision.getVersionList called; uuid: {uuid}")
    return JsonResponse(Revision.listRevisions(uuid,isComponent,field))


def revisionGetText(id,isComponent,fieldName,version):
    try:
        p = Revision.objects.get(parentId=id,fieldName=fieldName,version=version)
        text = p.fieldText
        print(text)
    except Revision.DoesNotExist:
        raise RevisionError("Revision does not exist for this ID/fieldname/version combo")
    return text



@csrf_protect
@require_http_methods(['POST'])
def revisionCompare(request):
    id = request.POST["uuid"]

    # todo: validate all user input
    currentText = request.POST["currentText"]
    toVersion = request.POST["toVersion"]
    fromVersion = str(request.POST["fromVersion"])
    toVersion = str(request.POST["toVersion"])
    fieldName = request.POST["fieldName"]
    isComponent = bool(request.POST["isComponent"])

    log.debug("Views.revisionCompare called; UUID: %s (fieldName: %s, toVersion: %s, fromVersion: %s)" % (id,fieldName,toVersion,fromVersion))


    if int(fromVersion) == -1:
        fromText = currentText
    else:
        fromText = revisionGetText(id,isComponent,fieldName,fromVersion)

    if int(toVersion) == -1:
        toText = currentText
    else:
        toText = revisionGetText(id,isComponent,fieldName,toVersion)

    diffHTML = Revision.diff(fromText,toText)
   # diffJSON = Revision.diff(toText,fromText)

    diffJSON = {}
    diffJSON['unifiedDiff'] = base64.urlsafe_b64encode(bytes(diffHTML,'utf-8')).decode('ascii')
    diffJSON['fromText'] = base64.urlsafe_b64encode(bytes(fromText,'utf-8')).decode('ascii')
    return JsonResponse(diffJSON)

@require_http_methods(['GET'])
def engagementNew(request):
    log.debug(f"engagementNew called")
    return render(request,"pages/engagementNew.html",{"form": EngagementForm})


@csrf_protect
@require_http_methods(['POST'])
def engagementCreate(request):
    
    p = Engagement.new(request.POST)
    p.name = request.POST.getlist("name")[0]
    p.save()
    response = HttpResponse(escape(p.name))
    response.status_code = 200
    log.debug(f'engagementCreate called, resulting engagement UUID: {p.id}')

    '''
    response = HttpResponse()
    response.status_code = 400
    log.debug(f'engagementCreate called, failed to create engagement')
    '''

    return response



@csrf_protect
@require_http_methods(['GET', 'POST'])
def engagementEdit(request,uuid):

    engagement = Engagement.get(id=uuid)

    if request.method == 'GET':
        # instantiate a cvssFinding object by passing in an instance of the model
        #findingsForm = CVSSForm(engagementId=engagement.id)
        log.debug(f'engagementEdit (GET) called, loading data for engagement with UUID: {engagement.id}')
        return render(request,"pages/engagementEdit.html",{
            'engagement': engagement,
            'findingDownloadExcel': f'/engagements/{engagement.id}/excel',
            'fgroupAdd': f'/engagements/'

        })
        # "form":form,"isApproved":cvssFinding.isApproved

    elif request.method == 'POST':
        log.debug(f'engagementEdit (POST) called, attempting to save data for engagement with UUID: {engagement.id}')
        engagement.updateFromPostData(request.POST)
        engagement.save()
        return HttpResponseRedirect('/engagements')


@csrf_protect
def engagementClone(request,uuid):

    log.debug(f'engagementClone called, Cloning: {uuid}')

    try:
        engagement = Engagement.get(id=uuid)
        engagementClone = engagement.clone()
        engagementClone.save()

    except Engagement.DoesNotExist:
        log.debug(f'engagementClone called, failed for  UUID: {p.id} (DOES NOT EXIST)')
        raise EngagementError("Specified Engagement does not exist")

    return HttpResponseRedirect("/engagements")


@csrf_protect
def engagementDelete(request,uuid):
    try:
        p = Engagement.get(id=uuid)

        # delete all findings groups associated with the engagement
        for findingGroup in p.fgroups:
            findingGroup.delete()
        p.delete()
        log.debug(f'engagementDelete called, succeeded for  UUID: {p.id}')
    except Engagement.DoesNotExist:
        log.debug(f'engagementDelete called, failed for  UUID: {p.id} (DOES NOT EXIST)')
        raise EngagementError("Specified Engagement does not exist")
    return HttpResponseRedirect("/engagements")


# Displays the list of existing reports and allows for the creation of a new one
@csrf_protect
@require_http_methods(['GET', 'POST'])
def engagementsList(request):
    engagements = Engagement.objects.all()
    if request.method == 'GET':
        log.debug(f'enagagementsList (GET) called')
        return render(request,"pages/engagements.html",{'engagements':engagements})

    elif request.method == 'POST':
        engagementsList = []
        for engagement in engagements:
            engagementsList.append(str(engagement.id))
        log.debug(f'enagagementsList (POST) called')
        return JsonResponse(engagementsList)


#commenting out for now. we decided we didnt want to clone the object, just pre-populate the form
# create a new engagementFinding based a findings database finding UUID and return the engagementfinding UUID
#def engagementCVSSFindingImport(request,uuid):
#    newEngagementFinding = CVSSDatabaseFinding.get(uuid).clone(name='',destinationClass=CVSSEngagementFinding)
#    return HttpResponse(newEngagementFinding.id)



# create a new Finding group (fgroup)
@csrf_protect
@require_http_methods(['POST'])
def engagementFgroupCreate(request,uuid,gtype):

    if gtype == "dread":
        p = DREADFindingGroup.new(uuid=uuid,postData=request.POST)
    elif gtype == "cvss":
        p = CVSSFindingGroup.new(uuid=uuid,postData=request.POST)
    elif gtype == "proactive":
        p = ProactiveFindingGroup.new(uuid=uuid,postData=request.POST)
    else:
        raise EngagementFgroupError("Fgroup type is not valid")

    p.save()
    log.debug(f'engagementFgroupCreate called, resulting Fgroup UUID {p.id} assigned to parent (engagement) id of {uuid}')
    return HttpResponse(p.id)


# Edit the name of a findingGroup
@csrf_protect
@require_http_methods(['POST'])
def engagementFgroupEdit(request,uuid):

    fgroup = BaseFindingGroup.get_child(id=uuid)
    log.debug(f'engagementFgroupEdit called, attempting to save data for Fgroup with UUID: {fgroup.id}')
    fgroup.updateFromPostData(request.POST, formClass=EditFgroupForm)
    fgroup.save()
    response = HttpResponse(f"Successfully updated findingsGroup {escape(str(uuid))}")
    response.status = 200
    return response


# Review which of the group's findings haven't been filled in
@csrf_exempt
def engagementFgroupStatus(request,uuid):

    fgroup = BaseFindingGroup.get_child(id=uuid)
    return render(request,"pages/findingGroupStatus.html",
                {
                    "fgroup":     fgroup,
                    "engagement": fgroup.engagement
                }
            )


# List all findingGroups (fgroups) associated with an engagement
@csrf_protect
@require_http_methods(['POST'])
def engagementFgroupList(request,uuid):
    fgroupsDict = {}
    log.debug(f"engagementFgroupList called for UUID {uuid}; request.method: {request.method}")

    CVSSFGroupList = []
    CVSSFgroups = CVSSFindingGroup.objects.filter(engagementParent=uuid)
    log.debug(list(CVSSFgroups))
    for i in CVSSFgroups:
        CVSSFGroupList.append({'id':str(i.id),'name':str(i.name)})
    fgroupsDict['CVSS'] = CVSSFGroupList

    DreadFGroupList = []
    DreadFgroups = DREADFindingGroup.objects.filter(engagementParent=uuid)
    log.debug(list(DreadFgroups))
    for i in DreadFgroups:
        DreadFGroupList.append({'id':str(i.id),'name':str(i.name)})
    fgroupsDict['DREAD'] = DreadFGroupList
    return JsonResponse(fgroupsDict)



@csrf_protect
@require_http_methods(['POST'])
def engagementFgroupDelete(request,uuid):

    fgroup = BaseFindingGroup.get_child(id=uuid)
    #fgroupChildren = fgroup.findingClass.objects.filter(findingGroup=uuid)
    #if fgroupChildren:
    #    log.debug(f"engagementFgroupDelete called for UUID {uuid}; DENIED:children detected")
   #     raise EngagementFgroupError("Could not delete: Children found")
    #else:
    #    log.debug(f"engagementFgroupDelete called for UUID {uuid}; Proceeding no children")
    # actually remove the findingsGroup
    fgroup.delete()
    response = HttpResponse(f"Successfully deleted findingsGroup {escape(str(uuid))}")
    response.status = 200
    return response



@csrf_protect
def engagementDelete(request,uuid):
    try:
        p = Engagement.get(id=uuid)
        p.delete()
        log.debug(f'engagementDelete called, succeeded for  UUID: {p.id}')
    except Engagement.DoesNotExist:
        log.debug(f'engagementDelete called, failed for  UUID: {p.id} (DOES NOT EXIST)')
        raise EngagementError("Specified Engagement does not exist")
    return HttpResponseRedirect("/engagements")



# Deletes the engagementFinding with the specified UUID
@csrf_protect
@require_http_methods(['GET', 'POST'])
def engagementFindingDelete(request,uuid):

    try:
        cvssEngagementFinding = CVSSEngagementFinding.get(uuid)
        name = cvssEngagementFinding.name
        cvssEngagementFinding.delete()
        response = HttpResponse(f'Successfully deleted cvssEngagementFinding "{escape(name)}"')
        response.status_code = 200
        return HttpResponseRedirect('/engagements/edit/%s' % str(cvssEngagementFinding.engagementParent))

    except CVSSEngagementFinding.DoesNotExist:
        log.debug(f'No report found with ID {uuid}')
        response.status_code = 400
        return response



    

#load an engagementFinding form up with data from a databaseFinding based on its UUID
@require_http_methods(['GET'])
def engagementFindingImport(request, fgroup, uuid):

    log.debug(f"engagementFindingImport called for findingGroup {fgroup} and uuid {uuid}")
    p = EngagementFinding.from_database(uuid, fgroup)

    p.populateForm()
    return render(
        request,
        'panes/engagementFindingNew.html',
        {
            "findingsForm": p.form,
            "categoryID": p.categoryID
        }
    )



#load an engagementFinding form up with data from a databaseFinding based on its UUID
@require_http_methods(['GET'])
def engagementFindingExport(request, uuid):

    log.debug(f"engagementFindingExport called for finding uuid {uuid}")
    p = EngagementFinding.get_child(id=uuid)

    if p.scoringType == 'CVSS':
         formClass = CVSSDatabaseFinding.formClass
    elif p.scoringType == 'DREAD':
        formClass = DREADDatabaseFinding.formClass
    elif p.scoringType == 'PROACTIVE':
        formClass = ProactiveDatabaseFinding.formClass

    p.populateForm(formClass=formClass)
    return render(
        request,
        'pages/findingNew.html',
        {
            "form": p.form,
            "categoryID": p.categoryID
        }
    )



#def engagementDREADFindingImport(request,uuid):
    #
#    newEngagementFinding = Finding.get(uuid).clone(name='',destinationClass=EngagementFinding)
#    return HttpResponse(newEngagementFinding)

# Given a findingGroup, return UUIDS for all associated engagmentFindings
@csrf_protect
def engagementFindingList(request,uuid):
    log.debug(f"engagementFindingList called for findingGroup {uuid}; request.method: {request.method}")


    engagementFindings = CVSSEngagementFinding.objects.filter(findingGroup=uuid)
    log.debug(list(engagementFindings))
    if request.method == 'GET':
        return render(request,"panes/engagementFindingsListManual.html",{'engagementFindings':engagementFindings})

    elif request.method == 'POST':
        engagementFindingsList = []
        for i in engagementFindings:
            log.debug("  Finding: {0}".format(i.id))
            engagementFindingsList.append(str(i.id))
        return JsonResponse(engagementFindingsList)


# Export all of the findings for this engagement to Excel format
@csrf_protect
@require_http_methods(['GET'])
def engagementFindingExcel(request,uuid):
    log.debug(f"engagementFindingExcel called for engagement UUID {uuid}; request.method: {request.method}")
    fgroups = Engagement.get(id=uuid).fgroups
    log.debug(list(fgroups))

    CVSSEngagementFindings = []
    DREADEngagementFindings = []
    ProactiveEngagementFindings = []
    for fgroup in fgroups:
        if fgroup.scoringType == "CVSS":
            CVSSEngagementFindings += fgroup.findings
        elif fgroup.scoringType == 'DREAD':
            DREADEngagementFindings += fgroup.findings
        elif fgroup.scoringType == 'PROACTIVE':
            ProactiveEngagementFindings += fgroup.findings

        else:
            raise EngagementError('Excel Export error: scoringType incorrectly assigned to findingGroup')


    # prepare response
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )

    response['Content-Disposition'] = f'attachment; filename=Engagement_{str(uuid)}.xlsx'
 
    
    # get finished workbook from excel.py
    workbook = generateExcel(
        CVSSEngagementFindings,
        DREADEngagementFindings,
        ProactiveEngagementFindings
    )
    workbook.save(response)
    return response




@csrf_protect
@require_http_methods(['POST', 'GET'])
def engagementFindingEdit(request, uuid):

    log.info(f"engagementFindingEdit called for UUID {uuid}; request.method: {request.method}")

    finding = EngagementFinding.get_child(uuid)
    
    if request.method == 'GET':
        finding.populateForm()
        return render(
            request,
            "pages/engagementFindingEdit.html",
            {
                'finding': finding,
            }
        )

    elif request.method == 'POST':
        log.debug(f"engagementFindingEdit POST request")
        finding.updateFromPostData(request.POST,finding.formClass)
        finding.save()
        return HttpResponse(finding.id)


# Deletes the engagementFinding with the specified UUID
@csrf_protect
@require_http_methods(['GET', 'POST'])
def engagementFindingDelete(request,uuid):
    log.debug(f"engagementFindingDelete called for finding ID: {uuid}")
    finding = EngagementFinding.get_child(uuid)

    name = finding.name
    finding.delete()
    log.debug(f"engagementFindingDelete sucesfully delete finding of type ({finding.className}) with name: {name}")
    response = HttpResponse(f'Successfully deleted finding of type ({escape(finding.className)}) with name "{escape(name)}"')
    response.status_code = 200
    return HttpResponseRedirect(f'/engagements/edit/{finding.fgroup.engagementParent}')



def engagementFindingNew(request, uuid):

    # discover the type of finding and load the appropriate page
    fgroup = BaseFindingGroup.get_child(id=uuid)
    findingsForm = fgroup.findingForm
    log.debug(f"engagementFindingNew called and used findingsForm class {findingsForm.className}")
    return render(
        request,
        "pages/engagementFindingNew.html",
        {
            "findingsForm": findingsForm,
            "fgroup": fgroup,
            "engagement": fgroup.engagement
        }
    )


@csrf_protect
def reportsList(request, uuid):
    log.debug(f"reportList called for UUID {uuid}; request.method: {request.method}")
    reports = Report.objects.filter(engagementParent=uuid)
    log.debug(f"reports: {reports}")
    if request.method == 'GET':
        return render(request, "panes/reportsList.html", {'engagementReports': engagementReports})
    
    elif request.method == 'POST':
        reportsList = []
        for i in reports:
            log.debug(f"  Report: {report.id}")
            reportsList.append(str(i.id))
        return JsonResponse(reportsList)


@csrf_protect
@require_http_methods(['POST'])
def engagementFindingCreate(request, uuid):

    fgroup = BaseFindingGroup.get_child(id=uuid)
    p = fgroup.findingClass.new(postData=request.POST, findingGroupParent=uuid)
    p.save()
    log.debug(f'engagementFindingCreate called, resolved to type ({fgroup.scoringType}) resulting engagementFinding UUID {p.id} and parent (fgroup) id of {uuid}')
    return HttpResponse(p.id)


# Displays the list of existing reports and allows for the creation of a new one
@csrf_protect
@require_http_methods(['GET', 'POST'])
def customersList(request):

    customers = Customer.objects.all()

    if request.method == 'GET':
        log.debug(f'customersList (GET) called')
        return render(request,"pages/customers.html",{'customers': customers})

    elif request.method == 'POST':
        log.debug(f'customersList (POST) called')
        return JsonResponse([str(c.id) for c in customers])


@csrf_protect
@require_http_methods(['POST'])
def customerCreate(request):
    
    c = Customer()
    c.updateFromPostData(request.POST)
    c.save()
    response = HttpResponse(escape(c.id))
    response.status_code = 200
    log.debug(f'customerCreate called, resulting customer UUID: {c.id}')

    return response


# Edit an existing "findings database" entry. Should be very similiar to findingsView, except with all the editing tools loaded.
@csrf_protect
@require_http_methods(['POST', 'GET'])
def customerEdit(request, uuid):

    customer = Customer.get(id=uuid)
    if request.method == 'GET':
        customer.populateForm()
        return render(request,"pages/customerEdit.html", {'customer': customer})

    elif request.method == 'POST':
        customer.updateFromPostData(request.POST)
        customer.save()
        return HttpResponse(customer.id)


@csrf_protect
@require_http_methods(['POST'])
def customerDelete(request, uuid):

    log.debug(f'Deleting customer with {uuid}')

    try:
        customer = Customer.get(id=uuid)
        log.debug(customer._json)
        customer.delete()
        return HttpResponse(customer.id)

    except Customer.DoesNotExist:
        log.debug(f'No customer found with ID {uuid}')
        response.status_code = 400
        return response



@require_http_methods(['GET'])
def templatesList(request):

    savedReports = []
    for r in SavedReport.objects.all():
        if r.modifiedDate:
            savedReport = SavedReport.get(id=r.id)
            savedReports.append(savedReport)

    pageTemplates = list(PageTemplate.objects.all())

    return render(
        request,
        "pages/savedReports.html",
        {
            'reports': savedReports,
            'pages': pageTemplates
        }
    )



# Saves a current report to a SavedReport 
@csrf_protect
@require_http_methods(['POST'])
def reportSaveToTemplate(request,uuid):

    # response = HttpResponse()
    #try:
    report = Report.objects.get(id=uuid)
    log.debug(f"reportSaveToTemplate; report.id: {report.id}")
    savedReport = report.clone(destinationClass=SavedReport)
    savedReport.simpleRedact(report.engagement.customer)
    savedReport.save()

    return HttpResponse(savedReport.id)

    #except Report.DoesNotExist:
    #log.debug(f'No report found with ID {uuid}')
    #response.status_code = 400
    #return response


# Clones a SavedReport to an engagement
@csrf_protect 
@require_http_methods(['POST'])
def reportCreateFromTemplate(request,uuid):

    engagementID = str(uuidlib.UUID(request.POST['engagementID']))
    savedReport = SavedReport.objects.get(id=uuid)
    log.debug(f"reportCreateFromTemplate; savedReport.id: {savedReport.id}")
    report = savedReport.clone(name=savedReport.name, destinationClass=Report)
    report.engagementParent = engagementID
    report.save()

    return HttpResponse(report.id)


# Loads the page where a user can select the components they want in their new reports (for templates)
@require_http_methods(['GET'])
def templateNew(request):
    log.debug(f"templateNew called;")
    componentList = settings.VALID_COMPONENTS
    return render(
        request,"pages/savedReportNew.html",
        {
            "componentsList": componentList,
            "report": BaseReport
        }
    )


      # Loads the page where a user can select the components they want in their new reports

@csrf_protect
@require_http_methods(['POST'])
def templateCreate(request):
    return reportCreate(request, None, fromTemplate=True)

# Given a reportID, get the JSON object containing the list of associated components
@require_http_methods(['GET'])
def templateEdit(request,uuid):
    log.debug("templateEdit() called; UUID: {0}".format(uuid))
    log.debug("Found {0} available components".format(len(settings.VALID_COMPONENTS)))
    savedReport = SavedReport.get(id=uuid)
    savedReport.populateForm()

    #print(savedReport._components)
    #print(savedReport)

    return render(request,"pages/savedReportEdit.html", \
        {
            "report": savedReport,
            "reportname": savedReport.name,
            "componentsList": settings.VALID_COMPONENTS
        })


# Page Templates

@require_http_methods(['GET'])
def pageNew(request):

    pageTemplate = PageTemplate()

    response = render(
        request,
        'pages/pageTemplateNew.html',
        {
            'page': pageTemplate
        }
    )

    return response

@csrf_protect
@require_http_methods(['POST'])
def pageCreate(request):
    
    pageTemplate = PageTemplate()
    form = pageTemplate.formClass(request.POST)
    pageTemplate.updateFromForm(form)
    pageTemplate.save()
    return HttpResponse(pageTemplate.id)


@csrf_protect
def pageEdit(request, uuid):
    
    pageTemplate = PageTemplate.get(id=uuid)
    pageTemplate.populateForm()

    response = render(
        request,
        'pages/pageTemplateEdit.html',
        {
            'page': pageTemplate
        }
    )

    return response

@csrf_protect
def pageDelete(request, uuid):
    
    pageTemplate = PageTemplate.get(id=uuid)
    pageTemplate.delete()
    return HttpResponse(f'Successfully deleted page "{escape(pageTemplate.name)}"')

@csrf_protect
def pageUpdate(request, uuid):
    
    pageTemplate = PageTemplate.get(id=uuid)
    form = pageTemplate.formClass(request.POST)
    pageTemplate.updateFromForm(form)
    pageTemplate.save()
    return HttpResponse(f'Successfully updated page "{escape(pageTemplate.name)}"')

@csrf_protect
def pageClone(request, uuid):

    page = PageTemplate.get(id=uuid)
    clonedPage = page.clone()
    clonedPage.save()
    log.debug("{0}".format(clonedPage))




    return HttpResponse(clonedPage.id)





# ----- Export / Import -----

def _serialize_mongo_doc(doc):
    result = {}
    for k, v in doc.items():
        if isinstance(v, uuidlib.UUID):
            result[k] = str(v)
        elif isinstance(v, datetime):
            result[k] = v.isoformat()
        elif isinstance(v, dict):
            result[k] = _serialize_mongo_doc(v)
        elif isinstance(v, list):
            result[k] = [
                _serialize_mongo_doc(i) if isinstance(i, dict)
                else str(i) if isinstance(i, uuidlib.UUID)
                else i for i in v
            ]
        else:
            result[k] = v
    return result


def _tree_uuids(tree):
    for node in tree:
        yield str(node['uuid'])
        if 'children' in node and node['children']:
            yield from _tree_uuids(node['children'])


def _import_component_tree(tree, component_data, new_report_id):
    new_tree = []
    for node in tree:
        old_uuid = str(node.get('uuid', ''))
        new_uuid = uuidlib.uuid4()
        new_node = {'type': node['type'], 'uuid': new_uuid}

        if old_uuid in component_data:
            doc = dict(component_data[old_uuid])
            doc['_id'] = new_uuid
            doc['reportParent'] = new_report_id
            if doc.get('databaseParent'):
                try:
                    doc['databaseParent'] = uuidlib.UUID(str(doc['databaseParent']))
                except (ValueError, AttributeError):
                    doc['databaseParent'] = None
            settings.MONGO_DB['report_components'].replace_one({'_id': new_uuid}, doc, upsert=True)

        if 'children' in node and node['children']:
            new_node['children'] = _import_component_tree(node['children'], component_data, new_report_id)

        new_tree.append(new_node)
    return new_tree


def _safe_filename(name, fallback='export'):
    return re.sub(r'[^\w\-_]', '_', name or fallback) + '.json'


# Report Template Export
@login_required
@require_http_methods(['GET'])
def templateExport(request, uuid):
    try:
        report = SavedReport.objects.get(id=uuid)
    except SavedReport.DoesNotExist:
        return HttpResponse('Template not found', status=404)

    try:
        component_tree = json.loads(report._components) if report._components else []
    except json.JSONDecodeError:
        component_tree = []

    component_data = {}
    for comp_uuid_str in _tree_uuids(component_tree):
        try:
            comp_uuid = uuidlib.UUID(comp_uuid_str)
            doc = settings.MONGO_DB['report_components'].find_one({'_id': comp_uuid})
            if doc is None:
                doc = settings.MONGO_DB['components'].find_one({'_id': comp_uuid})
            if doc:
                component_data[comp_uuid_str] = _serialize_mongo_doc(doc)
        except Exception:
            pass

    export_data = {
        'type': 'report_template',
        'version': '1.0',
        'name': report.name,
        'status': report.status,
        'pageTemplateID': str(report.pageTemplateID) if report.pageTemplateID else None,
        'component_tree': component_tree,
        'component_data': component_data,
    }

    response = HttpResponse(json.dumps(export_data, indent=2), content_type='application/json')
    response['Content-Disposition'] = f'attachment; filename="{_safe_filename(report.name)}"'
    return response


# Report Template Import
@login_required
@csrf_protect
@require_http_methods(['POST'])
def templateImport(request):
    if 'file' not in request.FILES:
        return HttpResponse('Missing file', status=400)
    try:
        data = json.loads(request.FILES['file'].read())
    except (json.JSONDecodeError, UnicodeDecodeError):
        return HttpResponse('Invalid JSON file', status=400)

    if data.get('type') != 'report_template':
        return HttpResponse('Invalid file type: expected report_template', status=400)

    new_report = SavedReport()
    new_report.name = escape(data.get('name', 'Imported Template'))
    new_report.status = data.get('status', 'active')
    new_report.save()

    component_tree = data.get('component_tree', [])
    component_data = data.get('component_data', {})
    new_tree = _import_component_tree(component_tree, component_data, new_report.id)
    new_report._components = json.dumps(new_tree, cls=UUIDEncoder)
    new_report.save()

    return HttpResponse(new_report.id)


# Page Template Export
@login_required
@require_http_methods(['GET'])
def pageExport(request, uuid):
    try:
        page = PageTemplate.objects.get(id=uuid)
    except PageTemplate.DoesNotExist:
        return HttpResponse('Page template not found', status=404)

    export_data = {
        'type': 'page_template',
        'version': '1.0',
        'name': page.name,
        'header': page.header or '',
        'footer': page.footer or '',
    }

    response = HttpResponse(json.dumps(export_data, indent=2), content_type='application/json')
    response['Content-Disposition'] = f'attachment; filename="{_safe_filename(page.name)}"'
    return response


# Page Template Import
@login_required
@csrf_protect
@require_http_methods(['POST'])
def pageImport(request):
    if 'file' not in request.FILES:
        return HttpResponse('Missing file', status=400)
    try:
        data = json.loads(request.FILES['file'].read())
    except (json.JSONDecodeError, UnicodeDecodeError):
        return HttpResponse('Invalid JSON file', status=400)

    if data.get('type') != 'page_template':
        return HttpResponse('Invalid file type: expected page_template', status=400)

    page = PageTemplate()
    page.name = escape(data.get('name', 'Imported Page Template'))
    page.header = data.get('header', '')
    page.footer = data.get('footer', '')
    page.default = False
    page.save()

    return HttpResponse(page.id)


# Customer Export
@login_required
@require_http_methods(['GET'])
def customerExport(request, uuid):
    try:
        customer = Customer.objects.get(id=uuid)
    except Customer.DoesNotExist:
        return HttpResponse('Customer not found', status=404)

    export_data = {
        'type': 'customer',
        'version': '1.0',
        'name': customer.name or '',
        'shortName': customer.shortName or '',
        'domain': customer.domain or '',
        'website': customer.website or '',
        'address': customer.address or '',
        'POC': customer.POC or '',
        'email': customer.email or '',
        'phone': customer.phone or '',
    }

    response = HttpResponse(json.dumps(export_data, indent=2), content_type='application/json')
    response['Content-Disposition'] = f'attachment; filename="{_safe_filename(customer.name, "customer")}"'
    return response


# Customer Import
@login_required
@csrf_protect
@require_http_methods(['POST'])
def customerImport(request):
    if 'file' not in request.FILES:
        return HttpResponse('Missing file', status=400)
    try:
        data = json.loads(request.FILES['file'].read())
    except (json.JSONDecodeError, UnicodeDecodeError):
        return HttpResponse('Invalid JSON file', status=400)

    if data.get('type') != 'customer':
        return HttpResponse('Invalid file type: expected customer', status=400)

    customer = Customer()
    customer.name = escape(data.get('name', 'Imported Customer'))
    customer.shortName = data.get('shortName', '')
    customer.domain = data.get('domain', '')
    customer.website = data.get('website', '')
    customer.address = data.get('address', '')
    customer.POC = data.get('POC', '')
    customer.email = data.get('email', '')
    customer.phone = data.get('phone', '')
    customer.save()

    return HttpResponse(customer.id)


def _user_form_data_from_user(user_obj):
    return {
        'username': user_obj.username or '',
        'first_name': user_obj.first_name or '',
        'last_name': user_obj.last_name or '',
        'email': user_obj.email or '',
        'is_active': user_obj.is_active,
        'is_staff': user_obj.is_staff,
        'is_superuser': user_obj.is_superuser,
    }


def _user_form_data_from_request(request, include_admin_fields=False):
    data = {
        'username': request.POST.get('username', '').strip(),
        'first_name': request.POST.get('first_name', '').strip(),
        'last_name': request.POST.get('last_name', '').strip(),
        'email': request.POST.get('email', '').strip(),
        'is_active': True,
        'is_staff': False,
        'is_superuser': False,
    }
    if include_admin_fields:
        data['is_active'] = request.POST.get('is_active') == 'on'
        data['is_staff'] = request.POST.get('is_staff') == 'on'
        data['is_superuser'] = request.POST.get('is_superuser') == 'on'
    return data


def _validate_passwords(password1, password2, require_password=False):
    errors = []
    if require_password and not password1:
        errors.append('Password is required.')
        return errors
    if password1 or password2:
        if password1 != password2:
            errors.append('Passwords do not match.')
        else:
            try:
                validate_password(password1)
            except ValidationError as e:
                errors.extend(e.messages)
    return errors


# Admin tools

@user_passes_test(lambda u: u.is_superuser)
@require_http_methods(['GET'])
def admintoolsHome(request):
    log.debug(f"adminHome called")
    users = User.objects.order_by('username')
    return render(request,"pages/admin.html",{'users': users})


@user_passes_test(lambda u: u.is_superuser)
@require_http_methods(['GET'])
def admintoolsBackup(request):
    log.debug(f"admintoolsBackup called")
    zipfile = dbExport()
    response = HttpResponse()
    response.write(zipfile)
    response['Content-Disposition'] = 'attachment; filename={0}'.format('backup.zip')
    return response



@user_passes_test(lambda u: u.is_superuser)
@require_http_methods(['POST'])
@csrf_protect
def admintoolsRestore(request):
    log.debug(f"admintoolsRestore called")
    if request.FILES['file']:
        uploadedFile = request.FILES['file']
        resultText,resultCode = dbImport(uploadedFile)
        if resultCode == 1:
            response = HttpResponse('OK')
            response.status_code = 200
        elif resultCode == 2:
            response = HttpResponse(escape(resultText))
            response.status_code = 400
        else:
            response = HttpResponse(escape(resultText))
            response.status_code = 400
        return response  


    else:
        response = HttpResponse('Missing backup file')
        response.status_code = 400
        return response  


@user_passes_test(lambda u: u.is_superuser)
@csrf_protect
@require_http_methods(['GET', 'POST'])
def adminUserNew(request):
    if request.method == 'GET':
        return render(request, "pages/adminUserEdit.html", {
            'form_action': '/admintools/users/new',
            'form_data': {
                'username': '',
                'first_name': '',
                'last_name': '',
                'email': '',
                'is_active': True,
                'is_staff': False,
                'is_superuser': False,
            },
            'errors': [],
            'is_new': True,
            'header': 'New User',
        })

    form_data = _user_form_data_from_request(request, include_admin_fields=True)
    errors = []
    if not form_data['username']:
        errors.append('Username is required.')
    elif User.objects.filter(username=form_data['username']).exists():
        errors.append('Username is already in use.')

    password1 = request.POST.get('password1', '')
    password2 = request.POST.get('password2', '')
    errors.extend(_validate_passwords(password1, password2, require_password=True))

    if form_data['is_superuser'] and not form_data['is_staff']:
        form_data['is_staff'] = True

    if errors:
        return render(request, "pages/adminUserEdit.html", {
            'form_action': '/admintools/users/new',
            'form_data': form_data,
            'errors': errors,
            'is_new': True,
            'header': 'New User',
        }, status=400)

    user_obj = User.objects.create_user(
        username=form_data['username'],
        password=password1,
        email=form_data['email']
    )
    user_obj.first_name = form_data['first_name']
    user_obj.last_name = form_data['last_name']
    user_obj.is_active = form_data['is_active']
    user_obj.is_staff = form_data['is_staff']
    user_obj.is_superuser = form_data['is_superuser']
    user_obj.save()

    messages.success(request, f'User {user_obj.username} created.')
    return redirect(f'/admintools/users/{user_obj.id}/edit')


@user_passes_test(lambda u: u.is_superuser)
@csrf_protect
@require_http_methods(['GET', 'POST'])
def adminUserEdit(request, user_id):
    user_obj = get_object_or_404(User, id=user_id)

    if request.method == 'GET':
        return render(request, "pages/adminUserEdit.html", {
            'form_action': f'/admintools/users/{user_obj.id}/edit',
            'form_data': _user_form_data_from_user(user_obj),
            'errors': [],
            'is_new': False,
            'header': f'Edit User: {user_obj.username}',
        })

    form_data = _user_form_data_from_request(request, include_admin_fields=True)
    errors = []
    if not form_data['username']:
        errors.append('Username is required.')
    elif User.objects.filter(username=form_data['username']).exclude(id=user_obj.id).exists():
        errors.append('Username is already in use.')

    password1 = request.POST.get('password1', '')
    password2 = request.POST.get('password2', '')
    errors.extend(_validate_passwords(password1, password2, require_password=False))

    if form_data['is_superuser'] and not form_data['is_staff']:
        form_data['is_staff'] = True

    if errors:
        return render(request, "pages/adminUserEdit.html", {
            'form_action': f'/admintools/users/{user_obj.id}/edit',
            'form_data': form_data,
            'errors': errors,
            'is_new': False,
            'header': f'Edit User: {user_obj.username}',
        }, status=400)

    user_obj.username = form_data['username']
    user_obj.first_name = form_data['first_name']
    user_obj.last_name = form_data['last_name']
    user_obj.email = form_data['email']
    user_obj.is_active = form_data['is_active']
    user_obj.is_staff = form_data['is_staff']
    user_obj.is_superuser = form_data['is_superuser']
    if password1:
        user_obj.set_password(password1)
    user_obj.save()
    if password1 and user_obj.id == request.user.id:
        update_session_auth_hash(request, user_obj)

    messages.success(request, f'User {user_obj.username} updated.')
    return redirect(f'/admintools/users/{user_obj.id}/edit')


@user_passes_test(lambda u: u.is_superuser)
@csrf_protect
@require_http_methods(['POST'])
def adminUserToggleActive(request, user_id):
    user_obj = get_object_or_404(User, id=user_id)
    if user_obj.id == request.user.id:
        return HttpResponse('You cannot deactivate your own account.', status=400)
    user_obj.is_active = not user_obj.is_active
    user_obj.save()
    return JsonResponse({'is_active': user_obj.is_active})


@login_required
@csrf_protect
@require_http_methods(['GET', 'POST'])
def accountEdit(request):
    user_obj = request.user
    if request.method == 'GET':
        return render(request, "pages/account.html", {
            'form_action': '/account',
            'form_data': _user_form_data_from_user(user_obj),
            'errors': [],
        })

    form_data = _user_form_data_from_request(request, include_admin_fields=False)
    errors = []

    password1 = request.POST.get('password1', '')
    password2 = request.POST.get('password2', '')
    errors.extend(_validate_passwords(password1, password2, require_password=False))

    if errors:
        return render(request, "pages/account.html", {
            'form_action': '/account',
            'form_data': form_data,
            'errors': errors,
        }, status=400)

    user_obj.first_name = form_data['first_name']
    user_obj.last_name = form_data['last_name']
    user_obj.email = form_data['email']
    if password1:
        user_obj.set_password(password1)
    user_obj.save()
    if password1:
        update_session_auth_hash(request, user_obj)

    messages.success(request, 'Account updated.')
    return redirect('/account')

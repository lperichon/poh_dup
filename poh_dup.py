import requests
import os
import face_recognition
import sys
from datetime import datetime
import time
import functools

graph_url = "https://api.thegraph.com/subgraphs/name/kleros/proof-of-humanity-mainnet"
ipfs_url = "https://ipfs.kleros.io"

# Get all submissions with their registration request
page_size = 1000
registered_query = """
    query indexQuery(
      $skip: Int = 0
      $first: Int = %s
      $where: Submission_filter
    ) {
      submissions(orderBy: creationTime, orderDirection: desc, where: $where, skip: $skip, first: $first) {
        id
        ...submissionCardSubmission
      }
    }

    fragment submissionCardSubmission on Submission {
      id
      status
      registered
      submissionTime
      name
      disputed
      requests(orderBy: creationTime, orderDirection: desc, first: 1, where: {registration: true}) {
        evidence(orderBy: creationTime, first: 1) {
          URI
          id
        }
        id
      }
    }
  """ % str(page_size)

# Get a submission with its corresponding registration request by id
by_address_query = """
  query IdQuery(
    $id: ID!
  ) {
    
    submission(id: $id) {
      name
      status
      registered
      submissionTime
      disputed
      ...submissionDetailsCardSubmission
      id
    }
    
  }

  fragment submissionDetailsCardSubmission on Submission {
    id
    status
    registered
    submissionTime
    name
    disputed
    requests(orderBy: creationTime, orderDirection: desc, first: 1, where: {registration: true}) {
      lastStatusChange
      evidence(orderBy: creationTime, first: 1) {
        URI
        id
      }
      id
    }
  }
"""

request_body = {'query': registered_query, 'variables': {"where": {"registered": True}}}

try:
  now = time.mktime(datetime.now().timetuple())
  data = open('./lastrun.log', 'rt')
  lastrun = data.readline(10)
  lastrun_datetime = datetime.fromtimestamp(int(lastrun))
  # If we already ran, then try to find only newly registered
  request_body['variables']['where']['submissionTime_gte'] = int(lastrun)
  print('Getting registration data since ' + lastrun_datetime.strftime("%d-%b-%Y (%H:%M:%S.%f)"))
except IOError:
  # otherwise get all
  print('Getting registration data (this could take a while)')
  
getmore = True
page = 0
while getmore :
  request_body['variables']['skip'] = page*page_size
  get = requests.post(
    url=graph_url,
    json=request_body
  )

  if get.status_code == 200:
    submissions = get.json()['data']['submissions']
    if len(submissions) == 0:
      getmore = False
      print("Done!")
      # store time for future runs
      open('./lastrun.log', 'wb').write(str(now))
    else:
      page = page + 1
      for submission in submissions:
        try:
          data = open('./data/' + submission['id'], 'r')
          data.close()
        except IOError:
          sys.stdout.write('.')
          sys.stdout.flush()
          evidence_url = ipfs_url + submission['requests'][0]['evidence'][0]['URI']
          get2 = requests.get(evidence_url)
          if get2.status_code == 200:
            evidence = get2.json()
            registration_url = ipfs_url + evidence['fileURI']
            get3 = requests.get(registration_url)
            if get3.status_code == 200:
              registration = get3.json()

              photo_url = ipfs_url + registration['photo']
              photo_data = requests.get(photo_url)

              if photo_data.status_code == 200:
                photo_file = open('./data/' + submission['id'], 'wb').write(photo_data.content)
              else:
                print("Error getting photo")
                sys.exit()
            else:
              print("Error getting registration")
              sys.exit()
          else:
            print("Error getting evidence")
            sys.exit()
  else:
    print("Error getting submissions")
    sys.exit()

print('Downloading registration photo for ' + sys.argv[1:][0])
get = requests.post(
  url=graph_url,
  json={'query': by_address_query, 'variables': {'id': sys.argv[1:][0]}}
)

if get.status_code == 200:
  submission = get.json()['data']['submission']
  
  try:
    data = open('./data/' + submission['id'], 'r')
    data.close()
  except IOError:
    evidence_url = ipfs_url + submission['requests'][0]['evidence'][0]['URI']
    get2 = requests.get(evidence_url)
    if get2.status_code == 200:
      evidence = get2.json()
      registration_url = ipfs_url + evidence['fileURI']
      get3 = requests.get(registration_url)
      if get3.status_code == 200:
        registration = get3.json()

        photo_url = ipfs_url + registration['photo']
        photo_data = requests.get(photo_url)

        if photo_data.status_code == 200:
          photo_file = open('./data/' + submission['id'], 'wb').write(photo_data.content)
        else:
          print("Error getting photo")
          sys.exit()
      else:
        print("Error getting registration")
        sys.exit()
    else:
      print("Error getting evidence")
      sys.exit()

  print('Loading data for face recognition (this could take a while)')

  # encode faces
  unknown_picture = face_recognition.load_image_file("./data/" + sys.argv[1:][0])
  unknown_face_encoding = face_recognition.face_encodings(unknown_picture)[0]
  sys.stdout.write('.')
  sys.stdout.flush()

  known_ids = []
  known_encodings = []

  for filename in os.listdir('./data'):
    if filename != sys.argv[1:][0] and filename != '.gitignore':
      picture = face_recognition.load_image_file("./data/" + filename)
      face_encoding = face_recognition.face_encodings(picture)
      #TODO find out why some files cant be encoded
      if len(face_encoding) > 0:
        sys.stdout.write('.')
        sys.stdout.flush()
        known_encodings.append(face_encoding[0])
        known_ids.append(filename)

  print("Done!")
  # See how far apart the test image is from the known faces
  print('Checking for duplicates of https://app.proofofhumanity.id/profile/' + sys.argv[1:][0]) + ' between ' + str(len(known_ids)) + ' registered humans'
  
  face_distances = face_recognition.face_distance(known_encodings, unknown_face_encoding)

  no_duplicates = functools.reduce(lambda a,b : a and b >= 0.6, face_distances)
  if no_duplicates:
    print('No duplicates found')
    sys.exit()

  for i, face_distance in enumerate(face_distances):
    if face_distance < 0.5:
      print('ALERT: this profile most likely duplicated! see: https://app.proofofhumanity.id/profile/' + known_ids[i])
    elif face_distance < 0.6:
      print('WARNING: this profile could be duplicated! see: https://app.proofofhumanity.id/profile/' + known_ids[i])
else:
  print('Error getting submission for', sys.argv[1:][0])
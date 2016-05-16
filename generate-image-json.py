#!/usr/bin/env python

from argparse import ArgumentParser
from base64 import b64encode, b64decode
from json import dumps, loads
from requests import get, put

insta_self_recent = 'https://api.instagram.com/v1/users/self/media/recent/'
github_json_file = 'https://api.github.com/repos/dhertz/dhertz.com/contents/static/photos.json'

def main(args):
  instagram = Instagram(args.insta_secret)
  images = instagram.get_my_media()

  contents_file = get_file_contents_github(args.github_secret)
  file_sha = contents_file['sha']

  #Decode the file from basse64 and load the json.
  existing_images = loads(b64decode(contents_file['content']))

  new_images = instagram.add_images(images, existing_images)
  if new_images:
    print("Commiting new file to github")
    #update_file_github(args.github_secret, file_sha, new_images + existing_images)

def get_file_contents_github(secret):
  # Get previous contents of file, and its SHA, so we can update it if need be
  req = get(github_json_file, params={'access_token':secret})
  if not req.status_code == 200:
    print("Could not retrive original file from GitHub")
    req.raise_for_status()
  return req.json()

def update_file_github(secret, file_sha, data):
  #PUT the new conent on github
  new_commit = {'message': 'Adding new instagram photo to json',
                'author': {
                  'name': "Daniel's Raspbery Pi",
                  'email': 'git@dhertz.com'
                },
                'content':b64encode(dumps(data)),
                'sha':file_sha
                }
  req = put(github_json_file, params={'access_token':secret},
    data=dumps(new_commit))
  if not req.status_code == 200:
    print("Could not update file in GitHub")
    req.raise_for_status()

class Instagram:
  def __init__(self, secret):
    self.secret = secret

  def add_images(self, images, existing_images):
    '''Function that recurses over the list of images,
      finding the first image that we already have in our repo, then adding
      the rest in reverse order. Also works when we start from scratch.

      TODO: make existing images ordered dict to to save iterating through it?
    '''

    if len(images) == 0:
      return []

    if images[0]['id'] not in [image['id'] for image in existing_images]:
      if len(images) == 1:
        images += self.get_my_media(images[0]['id'])
      images = [images[0]] + self.add_images(images[1:])
      return images
    else:
      return []

  def get_my_media(self, max_id=""):
    # Instagram paginates it's media, so we might have to make multiple requests
    req = get(insta_self_recent, params={'access_token':self.secret, 'max_id':max_id})
    if req.status_code == 200 and req.json()['meta']['code'] == 200:
      resp = req.json()
      images = []
      for m in resp['data']:
        title = m['caption']['text'] if m['caption'] else ''
        images.append({
                    'link':m['link'],
                    'large':m['images']['low_resolution']['url'],
                    'large_w':m['images']['low_resolution']['width'],
                    'small':m['images']['thumbnail']['url'],
                    'small_w':m['images']['thumbnail']['width'],
                    'id':m['id'],
                    'title':title
                  })
      print req.url
      return images
    else:
      print("Instagram API request failed!")
      req.raise_for_status()

if __name__ == '__main__':
  parser = ArgumentParser()
  parser.add_argument("--insta-secret",
    help="the instagram secret for your account", required=True)
  parser.add_argument("--github-secret",
    help="the github secret for your account", required=True)

  args = parser.parse_args()
  main(args)
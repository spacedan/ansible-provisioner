[![CADRE](/statics/images/cadre-logo.png)]()

[![](/../badges/master/build.svg)](/../commits/master)

# Introduction

CACI Deployment and Rapid-development Environment

CADRE provides a complete, state of the art cloud centric development and deployment environment, focused on web and mobile applications that enables Agile and DevOps style software lifecycle management.

This module includes a python script (deploy-jenkins.py) that translates the user's choices from the CADRE front end via json data file and deploys the CI/CD tools according to the options filled therein.

*Currently* only supports Jenkins, GoCD is planned to be added. 

This script is also intended for direct invocation by the front end javascript component, but can be used standalone if your `pipeline.json` file is set up properly.


# Setup

First, you must [install ansible](http://docs.ansible.com/ansible/latest/installation_guide/intro_installation.html)
Ansible is required to set up your jenkins host as well as any remote hosts. 

*Currently* This module assumes you have ssh key access (passwordless) to any hosts you are using as well as passwordless sudo. 

The playbook should work to install jenkins and docker locally or on the appropriate remote hosts. Currently only supports a linux deployment (Debian or RedHat) 


First time running the app
===

*Note: Windows users may need to run their command line as administrator to avoid permission errors relating to symlink creation.*

- Fork this repo.
- Clone your fork to a directory on your computer exclusive to CACI projects, e.g. a folder named CACI.
- Add a remote for the base repository you forked from. The recommended name for it is `base`.
  - Note: it is common to see the base repo referred to as `upstream` or `source` in other git projects.
  - Note: by default, you will already have the remote `origin` which refers to your fork.
- Configure `git` to use the correct email address for your projects:
  - Identify location of your global config: `git config --list --show-origin`. On \*nix systems, it is typically `~/.gitconfig`.
  - If you have a public GitHub account, alter your global config to add the email address associated with your GitHub account as your global default:

    ```
    [user]
        name = Your Name
        email = your_github@email_address.com
    ```
  - Add a line to your global config setting your CACI email address as the default for CACI projects:

    ```
    [includeIf "gitdir:~/Projects/CACI/"]
        path = ~/Projects/CACI/.gitconfig
    ```
  - Create the config file specified and add your CACI email address to it:

    ```
    [user]
        email = you@caci.com
    ```
- Run the CADRE front end module and fill in the appropriate options as directed. The CADRE front end can be found here: [CADRE](https://gitlab.ques.tech/CADRE/CADRE) 
- A file is produced named `pipeline.json`. This file can also be manually filled if you know what you are doing. A template is included in this repo.
- Run the python script as such: `python deploy-jenkins.py`
- The script produces the appropriate jenkins configurations and runs the ansible playbook as the current user against a produced inventory file if appropriate. 


Contributing
===

1. Create a branch in your fork for the feature or bug you're working on.
2. Do your work in your fork in the desired branch.
3. Commit your changes. The commit message should meaningfully and specifically describe your changes.
4. Fetch from all remotes.
5. Pull from the `base` remote.
6. Resolve any merge conflicts that may emerge.
7. Push your changes to your fork.
8. Open a merge request to the base repo from your fork. The merge request should meaningfully and specifically describe your changes. Note any issue(s) the MR closes by citing "closes #issue-number" in the MR text.


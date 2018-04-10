#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
deploy-jenkins.py

This program takes json input, converts and inputs it into various xml files,
and uses those to orhcestrate jenkins via ansible.

The program takes advantage of the emmetog.jenkins ansible role to deploy
jenkins once the xml configuration files are built.

TODO: Need a global list of jobs when creating a builder.
That list of jobs needs to be written to the ansible playbook
as the "jenkins_jobs" var.

TODO2: Some job names also need to be used in multiple methods, as some
job configs either trigger another job or are triggered by a job
Regarding this fact, some jobs are optional, so there may need to be
some conditional statements on wheather or not a job is included
"""

import json
import pdb
import os
import sys
import yaml
import logging
import xml.etree.cElementTree as ET
from xml.etree.ElementTree import parse, tostring
from xml.dom import minidom

class Builder(object):
    def __init__(self):
        self.logger = logging.getLogger('deploy-jenkins')
        hdlr = logging.FileHandler('deploy-jenkins.log')
        formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
        hdlr.setFormatter(formatter)
        self.logger.addHandler(hdlr)
        self.logger.setLevel(logging.INFO)

        jobs_list = []

    def replace_xml_element_text(self, xml_node, new_value):
        '''
        replace an xml node text with a new text value
        '''
        try:
            xml_node.text = new_value
        except:
            print("Error replacing xml text:", sys.exc_info()[0])
            raise

    def replace_yml_element_text(self, yml_node, new_value):
        '''
        replace a yml/yaml node text with a new value
        '''


    def write_xml_file(self, document, filename, create_parents=True, indent='  '):
        '''
        After replacing elements, write the new xml file and directories that contain it
        '''
        #pdb.set_trace()
        self.logger.info('attempting to write file {0}'.format(filename))
        if create_parents:
            directory = os.path.dirname(filename)
            if not os.path.exists(directory):
                os.mkdirs(directory)

        with open(filename, 'wb') as xml_file:
            #xml_file.write(document.tostring(), encoding='utf-8'))
            document.write(xml_file, encoding='utf-8')

    def modify_jenkins_config_xml(self, json_data, template='templates/jenkinsconfig.xml', config_file='jenkins-configs/config.xml'):
        """
        read from the json input file and create a config xml for jenkins
        TODO: Also change ansible playbook yml to replace jenkins version
        """
        jenkins_version = json_data['jenkins']['jenkins_version']
        app_name = json_data['app']['app_name']

        try:
            jenkins_config = parse(template)
        except OSError, e:
            print 'error parsing {0}'.format(template)

        #version = jenkins_config.getElementsByTagName('version')[0]
        version = jenkins_config.find('.//version')
        self.replace_xml_element_text(version, jenkins_version)

        pipeline_view_name = jenkins_config.find('.//name')
        self.replace_xml_element_text(pipeline_view_name, app_name)

        first_job = jenkins_config.find('.//firstJob')
        self.replace_xml_element_text(first_job, build_job_name)

        fjl = 'jobs/{0}'.format(build_job_name)
        first_job_link = jenkins_config.find('.//firstJobLink')
        self.replace_xml_element_text(first_job_link, fjl)

        #prettyxml = minidom.parseString(ET.tostring(config)).toprettyxml(indent="  ")
        #filename = 'jenkins-configs/config.xml'

        self.write_xml_file(jenkins_config, config_file)

    def modify_ansible_playbook(self, json_data, playbook_file='deploy-jenkins.yml'):
        """
        Read from the json input file and set up the ansible playook
        Need the following vars filled in the playbook:
            jenkins_jobs: a list of jobs that will be created in jenkins
            jenkins_version: string with the desired jenkins version
        """
        jenkins_version = json_data['jenkins']['jenkins_version']

        jenkins_jobs = jobs_list

        with open(playbook_file, 'w+') as f:
            playbook = yaml.load(f)
            playbook['vars'][0]['jenkins_version'] = jenkins_version
            playbook['vars'][0]['jenkins_jobs'] = jenkins_jobs
            f.write(yaml.dump(playbook, default_flow_style=False))

    def write_build_job_xml(self, json_data, template_file='templates/buildconfig.xml'):
        """
        For each of the build jobs, write the config xml with appropriate input from json
        TODO: Probably needs to be conditional if we are doing a local build or not,
        use a different template for local build vs. build on remote host
        """
        vc_type = json_data['app']['pipeline']['build_jobs']['version_control']['type']
        vc_url = json_data['app']['pipeline']['build_jobs']['version_control']['url']
        vc_branch = json_data['app']['pipeline']['build_jobs']['version_control']['branch']
        build_target = json_data['app']['pipeline']['build_jobs']['build_target']
        app_name = json_data['app']['app_name']

        #doc = parse('templates/buildconfig.xml')
        try:
            build_job_config = minidom.parse(template_file)
        except OSError, e:
            print 'error parsing {0}'.format(template_file)

        global build_job_name
        build_job_name = '{0}-build'.format(app_name)

        jobs_list.append(build_job_name)

        #git_url = doc.find('project/scm/UserRemoteConfigs/hudson.plugins.git.UserRemoteConfig/url')
        #git_url.text = str(vc_url)
        git_url = build_job_config.find('.//url')
        self.replace_xml_element_text(git_url, vc_url)

        #git_branch = doc.find('project/scm/branches/hudson.plugins.git.BranchSpec/name')
        #git_branch.text = str(vc_branch)
        git_branch = built_job_config.find('.//name')
        self.replace_xml_element_text(git_branch, vc_branch)

        build_command = 'docker build -t {0}:0.0.${BUILD_NUMBER} -t {1}:latest .'.format(app_name, app_name)
        command = build_job_config.find('.//command')
        self.replace_xml_element_text(command, build_command)

        #prettyxml = minidom.parseString(ET.tostring(doc)).toprettyxml(indent="  ")
        #directory = 'jenkins-configs/jobs/{0}-build'.format(app_name)
        #logger.info('creating job directory: {0}'.format(directory))
        #if not os.path.exists(directory):
        #    os.makedirs(directory)
        filename = 'jenkins-configs/jobs/{0}/config.xml'.format(build_job_name)
        #with open(filename, "w") as f:
        #    f.write(prettyxml)
        self.write_xml_file(build_job_config, filename)

    def write_deploy_job_xml(self, json_data, template_file='templates/deployconfig.xml'):
        """
        TODO: This method should populate the xml file with data for the deployment job
        The method may also need to modify the ansible playbook and hosts file
        Also have to modify the publish by ssh config file with the deployment target info
        NEED: build job name,
        app or container name for saving to tar (ex mage:latest),
        ssh host (config) name where we are deploying,
        deploy command string
        """
        app_name = json_data['app']['app_name']
        dev_environment = json_data['app']['pipeline']['deploy_jobs']['dev_environment']

        #build_job_name = '{0}-build'.format(app_name)
        local_command = 'docker save -o {0}.tar {0}:latest'.format(app_name)
        remote_command = 'docker load -i {0}.tar; docker-compose up -d'.format(app_name)

        try:
            deploy_job_config = minidom.parse(template_file)
        except OSError, e:
            print 'error parsing {0}'.format(template_file)

        project = deploy_job_config.find('.//project')
        self.replace_xml_element_text(project, build_job_name)

        command = deploy_job_config.find('.//command')
        self.replace_xml_element_text(command, local_command)

        remote_host = deploy_job_config.find('.//config')
        self.replace_xml_element_text(remote_host, dev_environment)

        exec_command = deploy_job_config.find('.//execCommand')
        self.replace_xml_element_text(exec_command, remote_command)

        global deploy_job_name
        deploy_job_name = '{0}-deploy'.format(app_name)

        jobs_list.append(deploy_job_name)

        filename = 'jenkins-configs/jobs/{0}/config.xml'.format(deploy_job_name)
        self.write_xml_file(deploy_job_config, filename)

    def write_ssh_config_template(self, json_data, template_file='templates/sshconfig.xml'):
        """
        Modify the ssh config file with data from the json file
        TODO: Need to include the authentication method. For now, would be best to include a field for
        ssh key in the json file and use that
        """
        ssh_config_filename = 'jenkins-configs/jenkins.plugins.publish_over_ssh.BapSshPublisherPlugin.xml'
        json_deploy_target = json_data['app']['pipeline']['deploy_job']['dev_environment']
        #json_deploy_username = json_data['app']['pipeline']['deploy_job']['username']
        #key = json_data['']

        try:
            ssh_config = minidom.parse(template_file)
        except OSError, e:
            print 'error parsing {0}'.format(template_file)

        config_name = ssh_config.find('.//name')
        config_hostname = ssh_config.find('.//hostname')
        config_username = ssh_config.find('.//username')
        self.replace_xml_element_text(config_name, json_deploy_target)
        self.replace_xml_element_text(config_hostname, json_deploy_target)
        #self.replace_xml_element_text(config_username, json_deploy_username)

        self.write_xml_file(ssh_config, ssh_config_filename)

    def write_unit_test_job_xml(self, json_data, template_file='templates/unittestconfig.xml'):
        """
        For each test job in the json, create a job config xml for jenkins
        """
        app_name = json_data['app']['app_name']
        test_command = json_data['app']['pipeline']['test_jobs']['unit_test']['test_command']
        test_target = json_data['app']['pipeline']['deploy_jobs']['dev_environment']

        doc = parse('templates/unittestconfig.xml')

        #build_trigger = doc.find('project/triggers/jenkins.triggers.ReverseBuildTrigger/upstreamProjects')
        #target = doc.find('project/builders/jenkins.plugins.publish__over__ssh.BapSshBuilderPlugin/delegate/delegate/publishers/jenkins.plugins.publish__over__ssh.BapSshPublisher/configName')
        #target = str(test_target)
        #command = doc.find('project/builders/jenkins.plugins.publish__over__ssh.BapSshBuilderPlugin/delegate/delegate/publishers/jenkins.plugins.publish__over__ssh.BapSshPublisher/transfers/jenkins.plugins.publish__over__ssh.BapSshTransfer/execCommand')
        #command = str(test_command)

        job_trigger = doc.find('.//upstreamProjects')
        self.replace_xml_element_text(job_trigger, deploy_job_name)

        target = doc.find('.//configName')
        self.replace_xml_element_text(target, test_target)

        docker_test_command = 'docker exec {0} {1}'.format(app_name, test_command)
        unit_test_command = doc.find('.//execCommand')
        self.replace_xml_element_text(unit_test_command, docker_test_command)

        unit_test_job_name = '{0}-unit-test'.format(app_name)
        unit_test_config = 'jenkins-configs/jobs/{0}/config.xml'.format(unit_test_job_name)

        jobs_list.append(unit_test_job_name)

        self.write_xml_file(doc, unit_test_config)

    def run_ansible_deployment(self, target, args, playbook='deploy-jenkins.yml'):
        """
        Run ansible playook command to launch jenkins locally
        TODO: change playbook to target the defined jenkins host if necessary
        """

        command = ['ansible-playbook', '-i', 'hosts', 'deploy-jenkins.yml']
        command.extend(args)
        #suprocess.call(command)
        print "Ansible Call: \n{0}".format(command)

def main():
    '''
    Temporary. This will be replaced by loading in the data directly from
    nodejs. Data will be extracted from json and implanted in the xml configs
    '''
    b = Builder()

    json_file = 'pipeline.json'
    b.logger.info('loading json file {0}'.format(json_file))
    with open(json_file) as myjson:
        json_data = json.load(myjson)
    b.logger.info('loaded json file')
    build_target = json_data['jenkins']['jenkins_host']
    app_name = json_data['app']['app_name']
    ansible_args = ''

    if build_target == 'localhost':
        deploylocal = True
        ansibleargs = '-c local'

    b.logger.info('Writing configs for app {0}'.format(app_name))
    b.modify_jenkins_config_xml(json_data)
    b.write_build_job_xml(json_data)
    b.write_deploy_job_xml(json_data)
    b.write_unit_test_job.xml(json_data)
    b.modify_ansible_playbook(json_data, 'deploy-jenkins.yml')
    b.run_ansible_deployment(build_target, ansible_args, "deploy-jenkins.yml")

if __name__ == "__main__":
    main()

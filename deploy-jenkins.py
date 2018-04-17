#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
deploy-jenkins.py

This program takes json input, converts and inputs it into various xml files,
and uses those to orhcestrate jenkins via ansible.

The program takes advantage of the emmetog.jenkins ansible role to deploy
jenkins once the xml configuration files are built.

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
import subprocess
from xml.etree.ElementTree import parse, tostring


class Builder(object):
    def __init__(self, json_filename):
        self.logger = logging.getLogger('deploy-jenkins')
        hdlr = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
        hdlr.setFormatter(formatter)
        self.logger.addHandler(hdlr)
        self.logger.setLevel(logging.INFO)

        with open(json_filename) as myjson:
            self.json_data = json.load(myjson)
        self.logger.info('loaded json file')
        jenkins_target = self.json_data['jenkins']['jenkins_host']
        jenkins_target_user = self.json_data['jenkins']['jenkins_host_user']
        self.app_name = self.json_data['app']['app_name']
        self.build_job_name = '{0}-build'.format(self.app_name)
        self.jobs_list = []

        self.inventory = {"jenkins": { "hosts": "", "vars": "" }}
        self.inventory["jenkins"]["hosts"] = jenkins_target
        self.inventory["jenkins"]["vars"] = 'ansible_ssh_user={0}'.format(jenkins_target_user)


    def replace_xml_element_text(self, xml_node, new_value):
        '''
        replace an xml node text with a new text value
        TODO: Add the xml doc and xpath string to find  and handle not found error
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
                os.makedirs(directory)

        with open(filename, 'wb') as xml_file:
            #xml_file.write(document.tostring(), encoding='utf-8'))
            document.write(xml_file, encoding='utf-8')

    def modify_jenkins_config_xml(self, template='templates/jenkinsconfig.xml', config_file='jenkins-configs/config.xml'):
        """
        read from the json input file and create a config xml for jenkins
        TODO: Also change ansible playbook yml to replace jenkins version
        """
        jenkins_version = self.json_data['jenkins']['jenkins_version']
        app_name = self.json_data['app']['app_name']

        try:
            jenkins_config = parse(template)
        except OSError, e:
            print 'error parsing {0}'.format(template)
            raise

        #version = jenkins_config.getElementsByTagName('version')[0]
        version = jenkins_config.find('.//version')
        self.replace_xml_element_text(version, jenkins_version)

        pipeline_view_name = jenkins_config.find('.//name')
        self.replace_xml_element_text(pipeline_view_name, app_name)

        first_job = jenkins_config.find('.//firstJob')
        self.replace_xml_element_text(first_job, self.build_job_name)

        fjl = 'jobs/{0}'.format(self.build_job_name)
        first_job_link = jenkins_config.find('.//firstJobLink')
        self.replace_xml_element_text(first_job_link, fjl)

        #ilename = 'jenkins-configs/config.xml'

        self.write_xml_file(jenkins_config, config_file)

    def modify_ansible_playbook(self, template='templates/playbook.yml', playbook_file='deploy-jenkins.yml'):
        """
        Read from the json input file and set up the ansible playook
        Need the following vars filled in the playbook:
            jenkins_jobs: a list of jobs that will be created in jenkins
            jenkins_version: string with the desired jenkins version
        """
        jenkins_version = self.json_data['jenkins']['jenkins_version']


        with open(template, 'r') as f:
            playbook = yaml.load(f)
        with open(playbook_file, 'wb') as f:
            #pdb.set_trace()
            playbook[0]['vars']['jenkins_version'] = jenkins_version
            playbook[0]['vars']['jenkins_jobs'] = self.jobs_list
            f.write(yaml.safe_dump(playbook, default_flow_style=False))

    def write_build_job_xml(self, template_file='templates/buildconfig.xml'):
        """
        For each of the build jobs, write the config xml with appropriate input from json
        TODO: Probably needs to be conditional if we are doing a local build or not,
        use a different template for local build vs. build on remote host
        """
        vc_type = self.json_data['app']['pipeline']['build_jobs']['version_control']['type']
        vc_url = self.json_data['app']['pipeline']['build_jobs']['version_control']['url']
        vc_branch = self.json_data['app']['pipeline']['build_jobs']['version_control']['branch']

        try:
            build_job_config = parse(template_file)
        except OSError, e:
            print 'error parsing {0}'.format(template_file)


        self.jobs_list.append(self.build_job_name)

        git_url = build_job_config.find('.//url')
        self.replace_xml_element_text(git_url, vc_url)

        git_branch = build_job_config.find('.//name')
        self.replace_xml_element_text(git_branch, vc_branch)

        build_command = 'docker build -t {0}:0.0.${{BUILD_NUMBER}} -t {0}:latest .'.format(self.app_name)
        command = build_job_config.find('.//command')
        self.replace_xml_element_text(command, build_command)

        #directory = 'jenkins-configs/jobs/{0}-build'.format(app_name)
        #logger.info('creating job directory: {0}'.format(directory))
        #if not os.path.exists(directory):
        #    os.makedirs(directory)
        filename = 'jenkins-configs/jobs/{0}/config.xml'.format(self.build_job_name)
        #with open(filename, "w") as f:
        #    f.write(prettyxml)
        self.write_xml_file(build_job_config, filename)

    def write_deploy_job_xml(self, template_file='templates/deployconfig.xml'):
        """
        TODO: This method should populate the xml file with data for the deployment job
        The method may also need to modify the ansible playbook and hosts file
        Also have to modify the publish by ssh config file with the deployment target info
        NEED: build job name,
        app or container name for saving to tar (ex mage:latest),
        ssh host (config) name where we are deploying,
        deploy command string
        """
        #app_name = json_data['app']['app_name']
        dev_environment = self.json_data['app']['pipeline']['deploy_jobs']['deploy_target']['config_name']

        local_command = 'docker save -o {0}.tar {0}:latest'.format(self.app_name)
        remote_command = 'docker load -i {0}.tar; docker-compose up -d'.format(self.app_name)

        try:
            deploy_job_config = parse(template_file)
        except OSError, e:
            print 'error parsing {0}'.format(template_file)

        project = deploy_job_config.find('.//project')
        self.replace_xml_element_text(project, self.build_job_name)

        command = deploy_job_config.find('.//command')
        self.replace_xml_element_text(command, local_command)

        remote_host = deploy_job_config.find('.//configName')
        self.replace_xml_element_text(remote_host, dev_environment)

        exec_command = deploy_job_config.find('.//execCommand')
        self.replace_xml_element_text(exec_command, remote_command)

        deploy_job_name = '{0}-deploy'.format(self.app_name)

        self.jobs_list.append(deploy_job_name)

        filename = 'jenkins-configs/jobs/{0}/config.xml'.format(deploy_job_name)
        self.write_xml_file(deploy_job_config, filename)
        return deploy_job_name

    def write_ssh_config(self, template_file='templates/sshconfig.xml'):
        """
        Modify the ssh config file with data from the json file
        TODO: Need to include the authentication method. For now, would be best to include a field for
        ssh key in the json file and use that
        """
        ssh_config_filename = 'jenkins-configs/jenkins.plugins.publish_over_ssh.BapSshPublisherPlugin.xml'
        json_deploy_target = self.json_data['app']['pipeline']['deploy_jobs']['deploy_target']['config_name']
        json_deploy_hostname = self.json_data['app']['pipeline']['deploy_jobs']['deploy_target']['hostname']
        json_deploy_username = self.json_data['app']['pipeline']['deploy_jobs']['deploy_target']['username']
        json_deploy_key = self.json_data['app']['pipeline']['deploy_jobs']['deploy_target']['key']

        try:
            ssh_config = parse(template_file)
        except OSError, e:
            print 'error parsing {0}'.format(template_file)
            raise

        config_name = ssh_config.find('.//name')
        config_hostname = ssh_config.find('.//hostname')
        config_username = ssh_config.find('.//username')
        config_key = ssh_config.find('.//key')
        self.replace_xml_element_text(config_name, json_deploy_target)
        self.replace_xml_element_text(config_hostname, json_deploy_target)
        self.replace_xml_element_text(config_username, json_deploy_username)
        self.replace_xml_element_text(config_key, json_deploy_key)
        self.write_xml_file(ssh_config, ssh_config_filename)

    def write_unit_test_job_xml(self, deploy_job_name, template_file='templates/unittestconfig.xml'):
        """
        For each test job in the json, create a job config xml for jenkins
        """
        test_command = self.json_data['app']['pipeline']['test_jobs']['unit_test']['test_command']
        test_target = self.json_data['app']['pipeline']['deploy_jobs']['deploy_target']['config_name']

        doc = parse('templates/unittestconfig.xml')

        job_trigger = doc.find('.//upstreamProjects')
        self.replace_xml_element_text(job_trigger, deploy_job_name)

        target = doc.find('.//configName')
        self.replace_xml_element_text(target, test_target)

        docker_test_command = 'docker exec {0} {1}'.format(self.app_name, test_command)
        unit_test_command = doc.find('.//execCommand')
        self.replace_xml_element_text(unit_test_command, docker_test_command)

        unit_test_job_name = '{0}-unit-test'.format(self.app_name)
        unit_test_config = 'jenkins-configs/jobs/{0}/config.xml'.format(unit_test_job_name)

        self.jobs_list.append(unit_test_job_name)

        self.write_xml_file(doc, unit_test_config)

    def run_ansible_deployment(self, playbook='deploy-jenkins.yml'):
        """
        Run ansible playook command to launch jenkins locally
        TODO: change playbook to target the defined jenkins host if necessary
        """

        if "localhost" in self.inventory["jenkins"]["hosts"]:
            ansible_args = '-c local'
        else:
            ansible_args = ''
        inventory_filename = 'hosts'

        self.logger.info('dumping inventory into file {0}'.format(inventory_filename))
        self.logger.info('Inventory: \n{0}'.format(json.dumps(self.inventory)))
        with open(inventory_filename, 'wb') as f:
            json.dump(self.inventory, f)
        if ansible_args:
            command = ['ansible-playbook', '-v', '-i', 'hosts', ansible_args, '--become', 'deploy-jenkins.yml']
        else:
            command = ['ansible-playbook', '-v', '-i', 'hosts', '--become', 'deploy-jenkins.yml']
        print "Ansible Call: \n{0}".format(command)
        self.run_command(command)

    def run_command(self, command):

        proc = subprocess.Popen(command,
                        stdin=subprocess.PIPE,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        )
        stdout_value, stderr_value = proc.communicate()
        self.logger.info('Stdout of command:\n{0}'.format(stdout_value))
        self.logger.info('Stderr of command:\n{0}'.format(stderr_value))

def main():
    '''
    Temporary. This will be replaced by loading in the data directly from
    nodejs. Data will be extracted from json and implanted in the xml configs
    '''

    json_file = 'pipeline.json'

    b = Builder(json_file)
    b.logger.info('loading json file {0}'.format(json_file))
    b.logger.info('Writing configs for app {0}'.format(b.app_name))
    b.modify_jenkins_config_xml()
    b.write_build_job_xml()
    my_deploy_job = b.write_deploy_job_xml()
    b.write_ssh_config()
    b.write_unit_test_job_xml(my_deploy_job)
    b.modify_ansible_playbook('templates/playbook.yml', 'deploy-jenkins.yml')
    b.run_ansible_deployment('deploy-jenkins.yml')

if __name__ == "__main__":
    main()

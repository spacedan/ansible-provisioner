#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
deploy-jenkins.py

This program takes json input, converts and inputs it into various xml files,
and uses those to orhcestrate jenkins via ansible.

The program takes advantage of the emmetog.jenkins ansible role to deploy
jenkins once the xml configuration files are built.
"""

import json
import os
import sys
import logging
import xml.etree.cElementTree as ET
from xml.etree.ElementTree import parse, tostring
from xml.dom import minidom

class Builder:
    def __init__(self):
        self.logger = logging.getLogger('jenkins_config')
        self.hdlr = logging.FileHandler('jenkins_config.log')
        self.formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
        hdlr.setFormatter(formatter)
        logger.addHandler(hdlr)
        logger.setLevel(logging.INFO)

    def replace_xml_element_text(node, new_value):
        '''
        replace an xml node text with a new text value
        '''
        try:
            node.firstChild.replaceWholeText(new_value.text)
        except:
            print("Error replacing xml text:", sys.exec_info()[0])
            raise

    def write_xml_file(document, filename, create_parents=True, indent='  '):
        '''
        After replacing elements, write the new xml file and directories that contain it
        '''
        logger.info('attempting to write file {0}'.format(filename))
        if create_parents:
            directory = os.path.dirname(filename)
            if not os.path.exists(directory):
                os.mkdirs(directory)

        with open(filename, 'wb') as xml_file:
            xml_file.write(document.string().toprettyxml(indent=indent, encoding='utf-8'))

    def modify_jenkins_config_xml(json_data, build_job_name, config_file='jenkins-configs/config.xml'):
        """
        read from the json input file and create a config xml for jenkins
        """
        jenkins_version = json_data['jenkins']['jenkins_version']
        app_name = json_data['app']['app_name']

        try:
            jenkins_config = minidom.parse(config_file)
        except OSError, e:
            print 'error parsing {0}'.format(config_file)

        version = jenkins_config.getElementsByTagName('version')[0]
        replace_xml_element_text(version, jenkins_version)

        #first_job = config.find('hudson/views/au.com.centrumsystems.hudson.plugin.buildpipeline.BuildPipelineView/gridBuilder/firstJob')
        #first_job.text = '{0}-build'.format(app_name)

        first_job = jenkins_config.getElementByTagName('firstJob')[0]
        replace_xml_element_text(first_job, build_job_name)

        #jenkins_config = open(config_file, "w+")

        #prettyxml = minidom.parseString(ET.tostring(config)).toprettyxml(indent="  ")
        #filename = 'jenkins-configs/config.xml'

        write_xml_file(minidom.parseString(ET.tostring(jenkins_config)), config_file)

    def write_build_job_xml(json_data, template_file='templates/buildconfig.xml'):
        """
        For each of the build jobs, write the config xml with appropriate input from json
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

        #git_url = doc.find('project/scm/UserRemoteConfigs/hudson.plugins.git.UserRemoteConfig/url')
        #git_url.text = str(vc_url)
        git_url = build_job_config.getElementByTagName('url')[0]
        replace_xml_element_text(git_url, vc_url)

        #git_branch = doc.find('project/scm/branches/hudson.plugins.git.BranchSpec/name')
        #git_branch.text = str(vc_branch)
        git_branch = built_job_config.getElementByTagName('name')[0]
        replace_xml_element_text(git_branch, vc_branch)

        #target = doc.find('project/builders/jenkins.plugins.publish__over__ssh.BapSshBuilderPlugin/delegate/delegate/publishers/jenkins.plugins.publish__over__ssh.BapSshPublisher/configName')
        #target = str(build_target)
        target = build_job_config.getElementByTagName('configName')[0]
        replace_xml_element_text(target, build_target.text)

        #prettyxml = minidom.parseString(ET.tostring(doc)).toprettyxml(indent="  ")
        #directory = 'jenkins-configs/jobs/{0}-build'.format(app_name)
        #logger.info('creating job directory: {0}'.format(directory))
        #if not os.path.exists(directory):
        #    os.makedirs(directory)
        filename = 'jenkins-configs/jobs/{0}/config.xml'.format(build_job_name)
        #with open(filename, "w") as f:
        #    f.write(prettyxml)
        write_xml_file(minidom.parseString(ET.tostring(build_job_config)), filename)

    def write_unit_test_job_xml(json_data, template_file='templates/unittestconfig.xml'):
        """
        For each test job in the json, create a job config xml for jenkins
        """
        app_name = json_data['app']['app_name']
        test_command = json_data['app']['pipeline']['test_jobs']['unit_test']['test_command']
        test_target = json_data['app']['pipeline']['deploy_jobs']['deploy_target']

        doc = parse('templates/unittestconfig.xml')

        #build_trigger = doc.find('project/triggers/jenkins.triggers.ReverseBuildTrigger/upstreamProjects')
        #target = doc.find('project/builders/jenkins.plugins.publish__over__ssh.BapSshBuilderPlugin/delegate/delegate/publishers/jenkins.plugins.publish__over__ssh.BapSshPublisher/configName')
        #target = str(test_target)
        #command = doc.find('project/builders/jenkins.plugins.publish__over__ssh.BapSshBuilderPlugin/delegate/delegate/publishers/jenkins.plugins.publish__over__ssh.BapSshPublisher/transfers/jenkins.plugins.publish__over__ssh.BapSshTransfer/execCommand')
        #command = str(test_command)

        job_trigger = doc.getElementByTagName('upstreamProjects')[0]
        replace_xml_element_text(job_trigger, build_job_name)

        target = doc.getElementByTagName('configName')[0]
        replace_xml_element_text(target, test_target)

        unit_test_command = doc.getElementByTagName('execCommand')
        replace_xml_element_text(unit_test_command, test_command)

        unit_test_job_name = '{0}-unit-test'.format(app_name)
        unit_test_config = 'jenkins-configs/jobs/{0}/config.xml'.format(unit_test_job_name)

        write_xml_file(minidom.parseString(ET.tostring(doc)), unit_test_config)

        #prettyxml = minidom.parseString(ET.tostring(doc)).toprettyxml(indent="  ")
        #directory = 'jenkins-configs/jobs/{0}-unit-test'.format(app_name)
        #if not os.path.exists(directory):
        #    os.makedirs(directory)
        #filename = '{0}/config.xml'.format(directory)
        #with open(filename, "w") as f:
        #    f.write(prettyxml)

    def build_jenkins(target, args):
        """
        Run ansible playook command to launch jenkins locally
        """
        command = ['ansible-playbook', '-i', 'hosts', 'deploy-jenkins.yml']
        command.extend(args)
        suprocess.call(command)

def main():
    '''
    Temporary. This will be replaced by loading in the data directly from
    nodejs. Data will be extracted from json and implanted in the xml configs
    '''

    json_file = 'pipeline.json'
    logger.info('loading json file '.format(json_file))
    json_data = json.load(open(json_file))
    build_target = json_data['jenkins']['jenkins_host']
    app_name = json_data['app']['app_name']
    ansible_args = ''

    if build_target == 'localhost':
        deploylocal = True
        ansibleargs = '-c local'

    myjsonfile = 'pipeline.json'
    json_data = json.load(open(myjsonfile))
    modify_jenkins_config_xml(json_data, "{0}-build".format(app_name))
    write_build_job_xml(json_data)
    write_unit_test_job.xml(json_data)


if __name__ == "__main__":
    main()

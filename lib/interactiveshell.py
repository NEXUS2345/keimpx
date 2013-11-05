#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
# -*- Mode: python -*-

from lib.common import *
from lib.smbshell import SMBShell

class InteractiveShell(cmd.Cmd):
    def __init__(self, target, credential, local_name, commands=None):
        '''
        Initialize the object variables
        '''

        cmd.Cmd.__init__(self)

        self.smb_shell = SMBShell(target, credential, local_name, commands)

        if isinstance(commands, (list, tuple, set)) and len(commands) > 0:
            logger.info('Executing commands from provided file')

            for command in commands:
                logger.debug('%s output:' % command)
                self.onecmd(command)
                logger.debug('----------8<----------')

            self.onecmd('exit')

        logger.info('Launching interactive SMB shell')
        self.prompt = '# '

        print 'Type help for list of commands'

    def cmdloop(self):
        while True:
            try:
                cmd.Cmd.cmdloop(self)
            except SessionError, e:
                #traceback.print_exc()
                logger.error('SMB error: %s' % (e.getErrorString(), ))
            except NetBIOSTimeout, e:
                logger.error('SMB connection timed out')
            except keimpxError, e:
                logger.error(e)
            except KeyboardInterrupt, _:
                print
                logger.info('User aborted')
                self.do_exit('')
            except Exception, e:
                #traceback.print_exc()
                logger.error(str(e))

    def emptyline(self):
        pass

    def complete_files(self, text, line, begidx, endidx, include=1):
        '''
        include means
        * 0: all files and directories
        * 1: just files
        * 2: just directories
        '''
        p = ntpath.normpath(line)

        if p.find('\\') < 0:
            items = []

            if include == 1:
                mask = 0
            else:
                mask = 0x010

            for i in self.smb_shell.completion:
                if i[1] == mask or include == 0:
                    items.append(i[0])

            if text:
                return [item for item in items if item.upper().startswith(text.upper())]
            else:
                return items

    def do_shell(self, cmd):
        '''
        Execute a local command if the provided command is preceed by an
        exclamation mark
        '''
        process = Popen(cmd, shell=True, stdout=PIPE, stderr=STDOUT)
        stdout, _ = process.communicate()

        if stdout is not None:
            print stdout

    def do_exit(self, line):
        '''
        Disconnect the SMB session
        '''
        self.smb_shell.logoff()
        sys.exit(0)

    def do_help(self, line):
        '''
        Show the help menu
        '''
        print '''Generic options
===============
help - show this message
verbosity {level} - set verbosity level (0-2)
info - returns NetrServerInfo main results
who - returns the sessions currently connected at the target host (admin required)
exit - terminates the SMB session and exit from the tool
!{command} - execute a local command

Shares options
==============
shares - list available shares
use {share} - connect to an specific share
cd {path} - changes the current directory to {path}
pwd - shows current remote directory
ls {path} - lists all the files in the current directory
cat {file} - display content of the selected file
download {filename} - downloads the filename from the current path
upload {filename} [destfile] - uploads the filename into a remote share (or current path)
rename {srcfile} {destfile} - rename a file
mkdir {dirname} - creates the directory under the current path
rm {file} - removes the selected file
rmdir {dirname} - removes the directory under the current path

Services options
================
services [service name] - list services
status {service name} - query the status of a service
query {service name} - list the configuration of a service
start {service name} - start a service
stop {service name} - stop a service
change {service name} - change the configuration of a service (in progress)
deploy {service name} {local file} [service args] [remote file] [displayname] - deploy remotely a service executable
undeploy {service name} - undeploy remotely a service executable

Users options
=============
users [domain] - list users, optionally for a specific domain
pswpolicy [domain] - list password policy, optionally for a specific domain
domains - list domains to which the system is part of

Registry options (Soon)
================
regread {registry key} - read a registry key
regwrite {registry key} {registry value} - add a value to a registry key
regdelete {registry key} - delete a registry key

Take-over options
=================
bindshell [port] - spawn an interactive shell on a TCP port on the target
      This works by upload a custom bind shell, executing it as a service
      and connecting to a TCP port where it listens, by default 4445/TCP.
      If the target is behind a strict firewall it will not work, rely on
      other techniques below instead.
svcshell [mode] - semi-interactive shell through a custom Windows Service
      This works by creating a service to execute a command, redirect its
      output to a temporary file within a share and retrieving its content,
      then deleting the service.
      Mode of operation can be SHARE (default) or SERVER whereby a local
      SMB server is instantiated to receive the output of the commands. This
      is useful in the situation where the target machine does not have a
      writeable share available - no extra ports are required.
atexec {command} - executes a command through the Task Scheduler service
      Returns the output of such command. Non-interactive shell, one command
      at a time - no extra ports are required.
psexec [command] - executes a command through SMB named pipes
      Same technique employed by Sysinternal's PsExec. The default command
      is cmd.exe therefore an interactive shell is established. It employs
      RemComSvc - no extra ports are required.
'''

    def do_verbosity(self, level):
        set_verbosity(level)

    def do_info(self, line):
        '''
        Display system information like operating system
        '''
        self.smb_shell.info()

    def do_who(self, line):
        '''
        Display the sessions currently connected at the target host (admin required)
        '''
        self.smb_shell.who()

    def do_shares(self, line):
        '''
        List available shares and display a menu to select which share to
        connect to
        '''
        self.smb_shell.shares()

    def do_use(self, share):
        '''
        Select the share to connect to
        '''
        self.smb_shell.use(share)

    def complete_cd(self, text, line, begidx, endidx):
        return self.complete_files(text, line, begidx, endidx, include=2)

    def do_cd(self, path):
        '''
        Change the current path
        '''
        self.smb_shell.cd(path)

    def do_pwd(self, line):
        '''
        Display the current path
        '''
        self.smb_shell.get_pwd()

    def do_dir(self, path):
        '''
        Alias to ls
        '''
        self.do_ls(path)

    def do_ls(self, path, display=True):
        '''
        List files from the current path
        '''
        self.smb_shell.ls(path, display)

    def complete_cat(self, text, line, begidx, endidx):
        return self.complete_files(text, line, begidx, endidx, include=1)

    def do_cat(self, filename):
        '''
        Display a file content from the current path
        '''
        self.smb_shell.cat(filename)

    def complete_get(self, text, line, begidx, endidx):
        return self.complete_files(text, line, begidx, endidx, include=1)

    def do_get(self, filename):
        '''
        Alias to download
        '''
        self.do_download(filename)

    def complete_download(self, text, line, begidx, endidx):
        return self.complete_files(text, line, begidx, endidx, include=1)

    def do_download(self, filename):
        '''
        Download a file from the current path
        '''
        self.smb_shell.download(filename)

    def do_put(self, pathname, destfile=None):
        '''
        Alias to upload
        '''
        self.do_upload(pathname, destfile)

    def do_upload(self, pathname, destfile=None):
        '''
        Upload a file in the current path
        '''
        if not destfile:
            argvalues = shlex.split(pathname)

            if len(argvalues) < 1:
                raise missingOption, 'You have to specify at least the local file name'
            elif len(argvalues) > 1:
                destfile = argvalues[1]

            pathname = argvalues[0]

        self.smb_shell.upload(pathname, destfile)

    def do_mv(self, srcfile, destfile=None):
        '''
        Alias to rename
        '''
        self.do_rename(srcfile, destfile)

    def do_rename(self, srcfile, destfile=None):
        '''
        Rename a file
        '''
        if not destfile:
            argvalues = shlex.split(srcfile)

            if len(argvalues) != 2:
                raise missingOption, 'You have to specify source and destination file names'
            else:
                srcfile, destfile = argvalues
                
        self.smb_shell.rename(srcfile, destfile)

    def do_mkdir(self, path):
        '''
        Create a directory in the current share
        '''
        self.smb_shell.mkdir(path)

    def complete_del(self, text, line, begidx, endidx):
        return self.complete_files(text, line, begidx, endidx, include=1)

    def do_del(self, filename):
        '''
        Alias to rm
        '''
        self.do_rm(filename)

    def complete_rm(self, text, line, begidx, endidx):
        return self.complete_files(text, line, begidx, endidx, include=1)

    def do_rm(self, filename):
        '''
        Remove a file in the current share
        '''
        self.smb_shell.rm(filename)

    def complete_rmdir(self, text, line, begidx, endidx):
        return self.complete_files(text, line, begidx, endidx, include=2)

    def do_rmdir(self, path):
        '''
        Remove a directory in the current share
        '''
        self.smb_shell.rmdir(path)

    def do_services(self, srvname):
        self.smb_shell.services(srvname)

    def do_status(self, srvname):
        if not srvname:
            raise missingService, 'Service name has not been specified'

        self.smb_shell.status(srvname)

    def do_query(self, srvname):
        if not srvname:
            raise missingService, 'Service name has not been specified'

        self.smb_shell.query(srvname)

    def do_start(self, srvname, srvargs=''):
        '''
        Start a service.
        '''
        if not srvargs:
            argvalues = shlex.split(srvname)

            if len(argvalues) < 1:
                raise missingService, 'Service name has not been specified'
            elif len(argvalues) > 1:
                srvargs = argvalues[1]

            srvname = argvalues[0]

        self.smb_shell.start(srvname, srvargs)

    def do_stop(self, srvname):
        '''
        Stop a service.
        '''
        if not srvname:
            raise missingService, 'Service name has not been specified'

        self.smb_shell.stop(srvname)

    def do_change(self, srvname):
        '''
        Change the configuration of a service.
        '''
        if not srvname:
            raise missingService, 'Service name has not been specified'

        self.smb_shell.change(srvname)

    def do_deploy(self, srvname, local_file=None, srvargs='', remote_file=None, displayname=None):
        '''
        Deploy a Windows service: upload the service executable to the
        file system, create a service as 'Automatic' and start it

        Sample command:
        deploy shortname contrib/srv_bindshell.exe 5438 remotefile.exe 'long name'
        '''
        argvalues = shlex.split(srvname)

        if len(argvalues) < 1:
            raise missingService, 'Service name has not been specified'

        srvname = argvalues[0]

        if not local_file:
            if len(argvalues) < 2:
                raise missingFile, 'Service file %s has not been specified' % local_file
            if len(argvalues) >= 5:
                displayname = argvalues[4]
            if len(argvalues) >= 4:
                remote_file = argvalues[3]
            if len(argvalues) >= 3:
                srvargs = argvalues[2]
            if len(argvalues) >= 2:
                local_file = argvalues[1]

        if not os.path.exists(local_file):
            raise missingFile, 'Service file %s does not exist' % local_file

        srvname = str(srvname)
        srvargs = str(srvargs)

        if not remote_file:
            remote_file = str(os.path.basename(local_file.replace('\\', '/')))
        else:
            remote_file = str(os.path.basename(remote_file.replace('\\', '/')))

        if not displayname:
            displayname = srvname
        else:
            displayname = str(displayname)

        self.smb_shell.deploy(srvname, local_file, srvargs, remote_file, displayname)

    def do_undeploy(self, srvname):
        '''
        Wrapper method to undeploy a Windows service. It stops the
        services, removes it and removes the executable from the file
        system
        '''
        if not srvname:
            raise missingService, 'Service name has not been specified'

        self.smb_shell.undeploy(srvname)

    def do_users(self, usrdomain):
        '''
        List users, optionally for a specific domain
        '''
        self.smb_shell.users(usrdomain)

    def do_pswpolicy(self, usrdomain):
        '''
        List password policy, optionally for a specific domain
        '''
        self.smb_shell.pswpolicy(usrdomain)

    def do_domains(self, line):
        '''
        List domains to which the system is part of
        '''
        self.smb_shell.domains()

    def do_bindshell(self, port):
        '''
        Spawn a shell listening on a TCP port on the target
        '''
        self.smb_shell.bindshell(port)

    def do_svcshell(self, mode='SHARE'):
        '''
        Semi-interactive shell through a custom Windows Service
        '''
        self.smb_shell.svcshell(mode)

    def do_atexec(self, command):
        '''
        Executes a command through the Task Scheduler service
        '''
        if not command:
            raise missingOption, 'Command has not been specified'

        self.smb_shell.atexec(command)

    def do_psexec(self, command):
        '''
        Executes a command through SMB named pipes
        '''
        self.smb_shell.psexec(command)

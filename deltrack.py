#!/usr/bin/env python3
# vim: set fileencoding=utf-8 :
# This prgram is Licenced under GPL, see http://www.gnu.org/copyleft/gpl.html
# Original author: Felix Hummel <deltrack@felixhummel.de>
# Rewritten for Clementine by Matthew Blissett <matt@blissett.me.uk>
# Thanks to Camille Gallet <camillegallet@yahoo.fr> for the infoamarok script,
# from which this script borrowed a lot.
import dbus
import sys
import subprocess
import logging
import os
import urllib.parse as urlparse

save = [".mp3", ".flac", ".wma", ".ogg", ".m4a"]  # Don't delete dir if it contains any of these files.
exts = [".tqd", ".mood"]  # Other extensions to delete with same base name.

log = logging.getLogger(__name__)


def main():
    try:
        bus = dbus.SessionBus()
    except:
        log.error("Could not connect to DBus.")
        sys.exit(1)
    try:
        clementine = bus.get_object('org.mpris.MediaPlayer2.clementine', '/org/mpris/MediaPlayer2')
        playerProperties = dbus.Interface(clementine, dbus_interface='org.freedesktop.DBus.Properties')
        player = dbus.Interface(clementine, dbus_interface='org.mpris.MediaPlayer2.Player')
    except:
        log.error("Could not connect to Clementine.")
        sys.exit(1)

    md = playerProperties.Get('org.mpris.MediaPlayer2.Player', 'Metadata')
    location = md['xesam:url']  # track's URL (to send track to trash)

    basename = os.path.splitext(location)[0]
    baseext = os.path.splitext(location)[1]
    exts.append(baseext)

    path = urlparse.urlparse(location).path
    dialog = subprocess.run(['kdialog', '--title', 'Delete currently playing file', '--yesno', 'Move %s to trash?' % urlparse.unquote(path)])
    if dialog.returncode > 0:
        log.info('Action cancelled')
        sys.exit(0)

    if playerProperties.Get('org.mpris.MediaPlayer2.Player', 'CanGoNext'):
        player.Next()
        # handle dynamic playlists. Thanks go to Oleg K (ICQ: 367607160)
        #new_index = tracklist.GetCurrentTrack()
        #if new_index == index:
        #    tracklist.DelTrack(index - 1)
        #else:
        #    tracklist.DelTrack(index)
    else:
        player.Stop()
        #tracklist.DelTrack(0)

    path = ''
    for ext in exts:  # Delete each basename+extension.
        loc = ''.join([basename, ext])
        filepath = urlparse.urlparse(loc).path  # Replace KDE's sillyness.
        print(filepath)
        if os.path.isfile(filepath):
            cmdext = ['kioclient5', 'move', loc, 'trash:/']
            log.info("Running %s" % ' '.join(cmdext))
            retcodext = subprocess.call(cmdext)
            path = urlparse.urlparse(loc).path
            if retcodext == 0:
                log.info('Successfully trashed "%s"' % path)
                subprocess.call(['kdialog', '--title', 'Music deleted', '--passivepopup', 'Successfully trashed ”%s”' % filepath, '5'])
            else:
                log.warn('Could not trash"%s"' % path)

    direc = os.path.split(path)[0]  # If the dir is empty let's get rid of it, as well.
    subdir = ''  # We'll set this below, if it exists.
    direc = urlparse.unquote(direc)  # Replace KDE's sillyness.
    # The following for loops seem a bit ugly, but this seems quicker than using recursion and ending up many levels deep,
    # and the various exists are off-putting, but we want to exit asap if we can.
    for f in os.listdir(direc):
        if os.path.isdir(os.path.join(direc, f)):  # We'll go one level deep, no more, takes time.
            subdir = os.path.join(direc, f)
            subls = os.listdir(subdir)
            if len(subls) > 15:  # We probably don't want to delete this.
                sys.exit(0)
            for s in subls:
                if os.path.isdir(os.path.join(subdir, s)):  # Only one level deep, so stop here.
                    sys.exit(0)
                if os.path.splitext(s)[1] in save:
                    sys.exit(0)
        if os.path.splitext(f)[1] in save:
            sys.exit(0)

    try:  # If we made it this far, nuke the dir/subdir.
        if subdir:
            rmdir = ['kioclient5', 'move', subdir, 'trash:/']
            retcodext = subprocess.call(rmdir)
            log.info("Removed empty subdir %s." % subdir)
        rmdir = ['kioclient5', 'move', direc, 'trash:/']
        retcodext = subprocess.call(rmdir)
        log.info("Removed empty dir %s." % direc)
    except OSError:
        log.error("Error removing %s, maybe no perms." % direc)

    sys.exit(0)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(levelname)s %(message)s')
    main()

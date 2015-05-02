#!/usr/bin/env python
# Filename: standards.py


__license__ = 'LGPLv3'
__copyright__ = 'Matthew McGowan, 2009'
__author__ = 'Matthew McGowan <matthew.joseph.mcgowan@gmail.com>'


class StandardIconNamingSpec:
    """
    Icon Naming Specification, Rodney Dawes
    <dobey@novell.com>
    Version 0.8
    http://standards.freedesktop.org/icon-naming-spec/icon-naming-spec-latest.html
    """

    def __init__(self):

        self.context_comments = {
            'actions': 'Icons which are generally used in menus and dialogs for interacting with the user.',
            'animations': 'Animated images used to represent loading web sites, or other background processing which may be less suited to more verbose progress reporting in the user interface.',
            'categories': 'Icons that are used for categories in the Programs menu, or the Control Center, for separating applications, preferences, and settings for display to the user.',
            'devices': 'Icons for hardware that is contained within or connected to the computing device.',
            'emblems': 'Icons for tags and properties of files, that are displayed in the file manager.',
            'emotes': 'Icons for emotions that are expressed through text chat applications such as :-) or :-P in IRC or instant messengers.',
            'international': 'Icons for international denominations such as flags.',
            'mimetypes': 'Icons for different types of data, such as audio or image files.',
            'places': 'Icons used to represent locations, either on the local filesystem, or through remote connections.',
            'status': 'Icons for presenting status to the user. This context contains icons for warning and error dialogs, as well as for the current weather, appointment alarms, and battery status.'
            }

        self.standard_names = {}
        self.standard_names['Actions'] = (
            'address-book-new',
            'application-exit',
            'appointment-new',
            'contact-new',
            'dialog-cancel',
            'dialog-close',
            'dialog-ok',
            'document-new',
            'document-open',
            'document-open-recent',
            'document-page-setup',
            'document-print',
            'document-print-preview',
            'document-properties',
            'document-revert',
            'document-save',
            'document-save-as',
            'edit-copy',
            'edit-cut',
            'edit-delete',
            'edit-find',
            'edit-find-replace',
            'edit-paste',
            'edit-redo',
            'edit-select-all',
            'edit-undo',
            'folder-new',
            'format-indent-less',
            'format-indent-more',
            'format-justify-center',
            'format-justify-fill',
            'format-justify-left',
            'format-justify-right',
            'format-text-direction-ltr',
            'format-text-direction-rtl',
            'format-text-bold',
            'format-text-italic',
            'format-text-underline',
            'format-text-strikethrough',
            'go-bottom',
            'go-down',
            'go-first',
            'go-home',
            'go-jump',
            'go-last',
            'go-next',
            'go-previous',
            'go-top',
            'go-up',
            'help-about',
            'help-contents',
            'help-faq',
            'insert-image',
            'insert-link',
            'insert-object',
            'insert-text',
            'list-add',
            'list-remove',
            'mail-forward',
            'mail-mark-important',
            'mail-mark-junk',
            'mail-mark-notjunk',
            'mail-mark-read',
            'mail-mark-unread',
            'mail-message-new',
            'mail-reply-all',
            'mail-reply-sender',
            'mail-send',
            'mail-send-receive',
            'media-eject',
            'media-playback-pause',
            'media-playback-start',
            'media-playback-stop',
            'media-record',
            'media-seek-backward',
            'media-seek-forward',
            'media-skip-backward',
            'media-skip-forward',
            'object-flip-horizontal',
            'object-flip-vertical',
            'object-rotate-left',
            'object-rotate-right',
            'system-lock-screen',
            'system-log-out',
            'system-run',
            'system-search',
            'tools-check-spelling',
            'view-fullscreen',
            'view-refresh',
            'view-restore',
            'view-sort-ascending',
            'view-sort-descending',
            'window-close',
            'window-new',
            'zoom-best-fit',
            'zoom-in',
            'zoom-original',
            'zoom-out'
            )

        self.standard_names['Animations'] = (
            'process-working',
            )

        self.standard_names['Application'] = (
            'accessories-calculator',
            'accessories-character-map',
            'accessories-dictionary',
            'accessories-text-editor',
            'help-browser',
            'multimedia-volume-control',
            'preferences-desktop-accessibility',
            'preferences-desktop-font',
            'preferences-desktop-keyboard',
            'preferences-desktop-locale',
            'preferences-desktop-multimedia',
            'preferences-desktop-screensaver',
            'preferences-desktop-theme',
            'preferences-desktop-wallpaper',
            'system-file-manager',
            'system-software-update',
            'utilities-system-monitor',
            'utilities-terminal'
            )

        self.standard_names['Categories'] = (
            'applications-accessories',
            'applications-development',
            'applications-engineering',
            'applications-games',
            'applications-graphics',
            'applications-internet',
            'applications-multimedia',
            'applications-office',
            'applications-other',
            'applications-science',
            'applications-system',
            'applications-utilities',
            'preferences-desktop',
            'preferences-desktop-peripherals',
            'preferences-desktop-personal',
            'preferences-other',
            'preferences-system',
            'preferences-system-network',
            'system-help'
            )

        self.standard_names['Devices'] = (
            'audio-card',
            'audio-input-microphone',
            'battery',
            'camera-photo',
            'camera-video',
            'computer',
            'drive-harddisk',
            'drive-optical',
            'drive-removable-media',
            'input-gaming',
            'input-keyboard',
            'input-mouse',
            'media-flash',
            'media-floppy',
            'media-optical',
            'media-tape',
            'modem',
            'multimedia-player',
            'network-wired',
            'network-wireless',
            'printer',
            'video-display'
            )

        self.standard_names['Emblems'] = (
            'emblem-default',
            'emblem-documents',
            'emblem-downloads',
            'emblem-favorite',
            'emblem-important',
            'emblem-mail',
            'emblem-photos',
            'emblem-readonly',
            'emblem-shared',
            'emblem-symbolic-link',
            'emblem-synchronized',
            'emblem-system',
            'emblem-unreadable'
            )

        self.standard_names['Emotes'] = (
            'face-angel',
            'face-crying',
            'face-devil-grin',
            'face-devil-sad',
            'face-glasses',
            'face-kiss',
            'face-monkey',
            'face-plain',
            'face-sad',
            'face-smile',
            'face-smile-big',
            'face-smirk',
            'face-surprise',
            'face-wink'
            )

        self.standard_names['International'] = (
            'flag-aa',
            )

        self.standard_names['MimeTypes'] = (
            'application-x-executable',
            'audio-x-generic',
            'font-x-generic',
            'image-x-generic',
            'package-x-generic',
            'text-html',
            'text-x-generic',
            'text-x-generic-template',
            'text-x-script',
            'video-x-generic',
            'x-office-address-book',
            'x-office-calendar',
            'x-office-document',
            'x-office-presentation',
            'x-office-spreadsheet'
            )

        self.standard_names['Places'] = (
            'folder',
            'folder-remote',
            'network-server',
            'network-workgroup',
            'start-here',
            'user-desktop',
            'user-home',
            'user-trash'
            )

        self.standard_names['Status'] = (
            'appointment-missed',
            'appointment-soon',
            'audio-volume-high',
            'audio-volume-low',
            'audio-volume-medium',
            'audio-volume-muted',
            'battery-caution',
            'battery-low',
            'dialog-error',
            'dialog-information',
            'dialog-password',
            'dialog-question',
            'dialog-warning',
            'folder-drag-accept',
            'folder-open',
            'folder-visiting',
            'image-loading',
            'image-missing',
            'mail-attachment',
            'mail-unread',
            'mail-read',
            'mail-replied',
            'mail-signed',
            'mail-signed-verified',
            'media-playlist-repeat',
            'media-playlist-shuffle',
            'network-error',
            'network-idle',
            'network-offline',
            'network-receive',
            'network-transmit',
            'network-transmit-receive',
            'printer-error',
            'printer-printing',
            'security-high',
            'security-medium',
            'security-low',
            'software-update-available',
            'software-update-urgent',
            'sync-error',
            'sync-synchronizing',
            'task-due',
            'task-passed-due',
            'user-away',
            'user-idle',
            'user-offline',
            'user-online',
            'user-trash-full',
            'weather-clear',
            'weather-clear-night',
            'weather-few-clouds',
            'weather-few-clouds-night',
            'weather-fog',
            'weather-overcast',
            'weather-severe-alert',
            'weather-showers',
            'weather-showers-scattered',
            'weather-snow',
            'weather-storm'
            )
        return

    def isstandard(self, context, icon):
        """
        Determines if the context and name passed exist in the standard dict.
        Returns True if context & name are in the Icon Naming Specification.
        """

        return self.standard_names.has_key(context) and \
            icon in self.standard_names[context]

    def get_context_comment(self, context):
        if self.context_comments.has_key(context.lower()):
            return self.context_comments[context.lower()]
        return None

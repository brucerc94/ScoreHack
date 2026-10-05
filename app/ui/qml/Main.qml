import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "components"

ApplicationWindow {
    id: window

    visible: true
    width: 1440
    height: 1000
    minimumWidth: 1440
    maximumWidth: 1440
    minimumHeight: 1000
    maximumHeight: 1000

    flags: Qt.Window
           | Qt.WindowTitleHint
           | Qt.WindowSystemMenuHint
           | Qt.WindowMinimizeButtonHint
           | Qt.WindowCloseButtonHint

    title: "ScoreHack — ScoreHack — Sheet Music Extractor"
    color: "#0a0f18"

    Dialog {
        id: errorDialog
        modal: true
        title: "Operation could not be completed"
        standardButtons: Dialog.Ok
        width: 520
        property string message: ""

        contentItem: Label {
            text: errorDialog.message
            color: "#dbe5f2"
            wrapMode: Text.WordWrap
            padding: 18
        }
    }

    Connections {
        target: backend
        function onError(message) {
            errorDialog.message = message
            errorDialog.open()
        }
    }

    RowLayout {
        anchors.fill: parent
        spacing: 0

        AppSidebar {
            Layout.preferredWidth: 190
            Layout.fillHeight: true
        }

        Item {
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true

            ColumnLayout {
                anchors.fill: parent
                anchors.leftMargin: 20
                anchors.rightMargin: 20
                anchors.topMargin: 8
                anchors.bottomMargin: 8
                spacing: 12

                RowLayout {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 54

                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 2

                        Label {
                            text: "Extract Sheet Music"
                            color: "#f4f7fb"
                            font.pixelSize: 28
                            font.bold: true
                        }

                        Label {
                            text: backend.status
                            color: "#7f90aa"
                            font.pixelSize: 13
                        }
                    }

                    BusyIndicator {
                        running: backend.busy
                        Layout.preferredWidth: 30
                        Layout.preferredHeight: 30
                    }
                }

                SourceCard {
                    Layout.preferredHeight: 125
                }

                RowLayout {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    spacing: 14

                    PreviewCard {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                    }

                    SettingsCard {
                        Layout.preferredWidth: 350
                        Layout.fillHeight: true
                    }
                }

                ActivityCard {
                    Layout.preferredHeight: 88
                }
            }
        }
    }
}

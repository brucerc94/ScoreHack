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

    title: "ScoreCapture — Extractor de Partituras"
    color: "#0a0f18"

    RowLayout {
        anchors.fill: parent
        spacing: 0

        AppSidebar {
            Layout.preferredWidth: 190
            Layout.fillHeight: true
        }

        ScrollView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            ScrollBar.horizontal.policy: ScrollBar.AlwaysOff

            ColumnLayout {
                width: Math.max(1180, parent.width - 40)
                x: 20
                spacing: 12

                RowLayout {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 54
                    Layout.topMargin: 10

                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 2

                        Label {
                            text: "Extraer una partitura"
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
                    Layout.preferredHeight: 650
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
                    Layout.preferredHeight: 90
                }

                Item { Layout.preferredHeight: 8 }
            }
        }
    }
}

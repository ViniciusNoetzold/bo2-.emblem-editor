"""
BO2 Emblem Studio - GUI Editor Main Window
===========================================
Main application window with PySide6.
"""

import sys
import os
from pathlib import Path
from typing import List, Optional

try:
    from PySide6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QSplitter, QTreeWidget, QTreeWidgetItem, QLabel, QPushButton,
        QFileDialog, QMessageBox, QSpinBox, QDoubleSpinBox, QComboBox,
        QColorDialog, QCheckBox, QGroupBox, QFormLayout, QScrollArea,
        QTabWidget, QToolBar, QStatusBar, QMenuBar, QMenu, QDockWidget,
        QLineEdit, QTextEdit, QProgressBar, QSlider, QFrame,
        QInputDialog, QStandardItemModel, QStandardItem
    )
    from PySide6.QtCore import Qt, QSize, QRect, Signal, Slot, QTimer
    from PySide6.QtGui import (
        QPixmap, QImage, QPainter, QColor, QPen, QBrush, QFont,
        QAction, QIcon, QPalette, QWheelEvent, QMouseEvent
    )
    HAS_PYSIDE6 = True
except ImportError:
    HAS_PYSIDE6 = False
    # Create dummy classes for type hints
    class QObject: pass
    class QWidget: pass
    class Signal: pass

from ..parser import EmblemLayer, EmblemParser
from ..serializer import EmblemSerializer
from ..renderer import EmblemRenderer
from ..importer import ImageImporter, ImportConfig
from ..exporter import EmblemExporter, ExportConfig
from ..optimizer import EmblemOptimizer, OptimizerConfig
from ..ai import EmblemAIGenerator
from ..shape_map import (
    SHAPE_ID_MAP, get_ids_by_category, get_shape_name, 
    CATEGORY_ORDER, get_category_display
)


if HAS_PYSIDE6:
    class ShapeListWidget(QTreeWidget):
        """Widget for displaying and selecting shapes."""
        
        shape_selected = Signal(int)
        
        def __init__(self):
            super().__init__()
            self.setHeaderLabels(["Shape", "ID"])
            self.setColumnWidth(0, 200)
            self.setColumnWidth(1, 60)
            self.itemClicked.connect(self._on_item_clicked)
            self._populate()
        
        def _populate(self):
            for cat in CATEGORY_ORDER:
                cat_item = QTreeWidgetItem([get_category_display(cat), ""])
                cat_item.setFlags(cat_item.flags() | Qt.ItemIsAutoTristate)
                cat_item.setExpanded(True)
                
                ids = get_ids_by_category(cat)
                for shape_id in ids:
                    name = get_shape_name(shape_id).split("/", 1)[1]
                    child = QTreeWidgetItem([name, str(shape_id)])
                    child.setData(0, Qt.UserRole, shape_id)
                    cat_item.addChild(child)
                
                self.addTopLevelItem(cat_item)
        
        def _on_item_clicked(self, item: QTreeWidgetItem, column: int):
            shape_id = item.data(0, Qt.UserRole)
            if shape_id is not None:
                self.shape_selected.emit(shape_id)


    class LayerListWidget(QTreeWidget):
        """Widget for displaying and managing emblem layers."""
        
        layer_selected = Signal(int)
        layers_reordered = Signal()
        
        def __init__(self):
            super().__init__()
            self.setHeaderLabels(["#", "Shape", "Color", "Pos", "Scale", "Rot", "O", "F"])
            self.setColumnWidth(0, 30)
            self.setColumnWidth(1, 150)
            self.setColumnWidth(2, 80)
            self.setColumnWidth(3, 80)
            self.setColumnWidth(4, 80)
            self.setColumnWidth(5, 50)
            self.setColumnWidth(6, 25)
            self.setColumnWidth(7, 25)
            self.setDragDropMode(QTreeWidget.InternalMove)
            self.itemClicked.connect(self._on_item_clicked)
            self.model().rowsMoved.connect(self._on_rows_moved)
            self.layers = []
        
        def set_layers(self, layers: List[EmblemLayer]):
            self.layers = layers
            self.clear()
            for layer in layers:
                self._add_layer_item(layer)
        
        def _add_layer_item(self, layer: EmblemLayer):
            shape_name = get_shape_name(layer.shape_id).split("/", 1)[1]
            color_str = f"#{int(layer.r*255):02X}{int(layer.g*255):02X}{int(layer.b*255):02X}"
            pos_str = f"{layer.pos_x:.2f}, {layer.pos_y:.2f}"
            scale_str = f"{layer.true_scale_x:.2f}, {layer.true_scale_y:.2f}"
            
            item = QTreeWidgetItem([
                str(layer.index),
                shape_name,
                color_str,
                pos_str,
                scale_str,
                f"{layer.rotation:.1f}°",
                "✓" if layer.outlined else "",
                "✓" if layer.flipped else ""
            ])
            item.setData(0, Qt.UserRole, layer.index)
            
            if layer.index % 2 == 0:
                for col in range(self.columnCount()):
                    item.setBackground(col, QColor(240, 240, 240))
            
            self.addTopLevelItem(item)
        
        def _on_item_clicked(self, item: QTreeWidgetItem, column: int):
            index = item.data(0, Qt.UserRole)
            if index is not None:
                self.layer_selected.emit(index)
        
        def _on_rows_moved(self):
            self.layers_reordered.emit()


    class PropertyPanel(QWidget):
        """Panel for editing layer properties."""
        
        property_changed = Signal(int, str, object)
        
        def __init__(self):
            super().__init__()
            self.current_layer = None
            self._setup_ui()
        
        def _setup_ui(self):
            layout = QVBoxLayout(self)
            
            self.layer_label = QLabel("No layer selected")
            self.layer_label.setFont(QFont("", 10, QFont.Bold))
            layout.addWidget(self.layer_label)
            
            # Shape
            shape_group = QGroupBox("Shape")
            shape_layout = QFormLayout(shape_group)
            
            self.shape_combo = QComboBox()
            self.shape_combo.currentIndexChanged.connect(self._on_shape_changed)
            self._populate_shapes()
            shape_layout.addRow("Shape:", self.shape_combo)
            layout.addWidget(shape_group)
            
            # Color
            color_group = QGroupBox("Color")
            color_layout = QFormLayout(color_group)
            
            self.color_btn = QPushButton()
            self.color_btn.setFixedSize(80, 30)
            self.color_btn.clicked.connect(self._choose_color)
            color_layout.addRow("Color:", self.color_btn)
            layout.addWidget(color_group)
            
            # Position
            pos_group = QGroupBox("Position")
            pos_layout = QFormLayout(pos_group)
            
            self.pos_x = QDoubleSpinBox()
            self.pos_x.setRange(-10, 10)
            self.pos_x.setSingleStep(0.01)
            self.pos_x.valueChanged.connect(lambda v: self._emit("pos_x", v))
            pos_layout.addRow("X:", self.pos_x)
            
            self.pos_y = QDoubleSpinBox()
            self.pos_y.setRange(-10, 10)
            self.pos_y.setSingleStep(0.01)
            self.pos_y.valueChanged.connect(lambda v: self._emit("pos_y", v))
            pos_layout.addRow("Y:", self.pos_y)
            layout.addWidget(pos_group)
            
            # Scale
            scale_group = QGroupBox("Scale (log2)")
            scale_layout = QFormLayout(scale_group)
            
            self.scale_x = QDoubleSpinBox()
            self.scale_x.setRange(-10, 10)
            self.scale_x.setSingleStep(0.01)
            self.scale_x.valueChanged.connect(lambda v: self._emit("scale_x", v))
            scale_layout.addRow("X:", self.scale_x)
            
            self.scale_y = QDoubleSpinBox()
            self.scale_y.setRange(-10, 10)
            self.scale_y.setSingleStep(0.01)
            self.scale_y.valueChanged.connect(lambda v: self._emit("scale_y", v))
            scale_layout.addRow("Y:", self.scale_y)
            layout.addWidget(scale_group)
            
            # Rotation
            rot_group = QGroupBox("Rotation")
            rot_layout = QFormLayout(rot_group)
            
            self.rotation = QDoubleSpinBox()
            self.rotation.setRange(0, 360)
            self.rotation.setSingleStep(1)
            self.rotation.valueChanged.connect(lambda v: self._emit("rotation", v))
            rot_layout.addRow("Degrees:", self.rotation)
            layout.addWidget(rot_group)
            
            # Flags
            flags_group = QGroupBox("Flags")
            flags_layout = QVBoxLayout(flags_group)
            
            self.outlined = QCheckBox("Outlined")
            self.outlined.toggled.connect(lambda v: self._emit("outlined", v))
            flags_layout.addWidget(self.outlined)
            
            self.flipped = QCheckBox("Flipped")
            self.flipped.toggled.connect(lambda v: self._emit("flipped", v))
            flags_layout.addWidget(self.flipped)
            layout.addWidget(flags_group)
            
            layout.addStretch()
        
        def _populate_shapes(self):
            self.shape_combo.addItem("Empty", 0xFFFF)
            for cat in CATEGORY_ORDER:
                cat_name = get_category_display(cat)
                cat_item = QStandardItem(cat_name)
                cat_item.setSelectable(False)
                self.shape_combo.model().appendRow(cat_item)
                
                ids = get_ids_by_category(cat)
                for shape_id in ids:
                    name = get_shape_name(shape_id).split("/", 1)[1]
                    item = QStandardItem(name)
                    item.setData(shape_id, Qt.UserRole)
                    cat_item.appendRow(item)
        
        def set_layer(self, layer: Optional[EmblemLayer]):
            self.current_layer = layer
            if layer is None:
                self.layer_label.setText("No layer selected")
                self.setEnabled(False)
                return
            
            self.setEnabled(True)
            self.layer_label.setText(f"Layer {layer.index}: {get_shape_name(layer.shape_id).split('/', 1)[1]}")
            
            self._block_signals(True)
            
            idx = self.shape_combo.findData(layer.shape_id, Qt.UserRole)
            if idx >= 0:
                self.shape_combo.setCurrentIndex(idx)
            
            self._update_color_btn(layer.r, layer.g, layer.b)
            
            self.pos_x.setValue(layer.pos_x)
            self.pos_y.setValue(layer.pos_y)
            
            self.scale_x.setValue(layer.scale_x)
            self.scale_y.setValue(layer.scale_y)
            
            self.rotation.setValue(layer.rotation)
            
            self.outlined.setChecked(layer.outlined)
            self.flipped.setChecked(layer.flipped)
            
            self._block_signals(False)
        
        def _block_signals(self, block: bool):
            for widget in [self.shape_combo, self.pos_x, self.pos_y, 
                           self.scale_x, self.scale_y, self.rotation,
                           self.outlined, self.flipped]:
                widget.blockSignals(block)
        
        def _on_shape_changed(self, index: int):
            shape_id = self.shape_combo.itemData(index, Qt.UserRole)
            if shape_id is not None and self.current_layer:
                self.property_changed.emit(self.current_layer.index, "shape_id", shape_id)
        
        def _choose_color(self):
            if not self.current_layer:
                return
            color = QColorDialog.getColor(
                QColor(int(self.current_layer.r * 255), 
                       int(self.current_layer.g * 255), 
                       int(self.current_layer.b * 255),
                       int(self.current_layer.a * 255)),
                self, "Choose Color"
            )
            if color.isValid():
                self._update_color_btn(color.redF(), color.greenF(), color.blueF())
                self.property_changed.emit(self.current_layer.index, "color", 
                                         (color.redF(), color.greenF(), color.blueF(), color.alphaF()))
        
        def _update_color_btn(self, r: float, g: float, b: float):
            color = QColor(int(r * 255), int(g * 255), int(b * 255))
            self.color_btn.setStyleSheet(f"background-color: {color.name()}; border: 1px solid #666;")
        
        def _emit(self, prop: str, value):
            if self.current_layer:
                self.property_changed.emit(self.current_layer.index, prop, value)


    class PreviewWidget(QLabel):
        """Widget for previewing the rendered emblem."""
        
        def __init__(self):
            super().__init__()
            self.setMinimumSize(512, 512)
            self.setAlignment(Qt.AlignCenter)
            self.setStyleSheet("background-color: #181818; border: 1px solid #444;")
            self.setScaledContents(True)
            self.layers = []
            self.renderer = EmblemRenderer()
            self._pixmap = None
        
        def set_layers(self, layers: List[EmblemLayer]):
            self.layers = layers
            self._render()
        
        def _render(self):
            if not self.layers:
                self.clear()
                return
            
            size = max(self.width(), self.height())
            img = self.renderer.render_png(self.layers, size=size, bg_color=(0, 0, 0, 0))
            
            img_data = img.tobytes("raw", "RGBA")
            qimg = QImage(img_data, img.width, img.height, QImage.Format_RGBA8888)
            self._pixmap = QPixmap.fromImage(qimg)
            self.setPixmap(self._pixmap.scaled(
                self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
        
        def resizeEvent(self, event):
            super().resizeEvent(event)
            self._render()


    class EmblemEditor(QMainWindow):
        """Main application window."""
        
        def __init__(self):
            super().__init__()
            self.setWindowTitle("BO2 Emblem Studio")
            self.resize(1400, 900)
            
            self.layers = []
            self.current_file = None
            
            self._setup_ui()
            self._setup_actions()
            self._setup_menu()
            self._setup_toolbar()
            self._setup_statusbar()
            
            self._new_emblem()
        
        def _setup_ui(self):
            central = QWidget()
            self.setCentralWidget(central)
            main_layout = QHBoxLayout(central)
            
            splitter = QSplitter(Qt.Horizontal)
            main_layout.addWidget(splitter)
            
            # Left panel
            left_widget = QWidget()
            left_layout = QVBoxLayout(left_widget)
            
            left_tabs = QTabWidget()
            
            self.shape_list = ShapeListWidget()
            self.shape_list.shape_selected.connect(self._on_shape_selected)
            left_tabs.addTab(self.shape_list, "Shapes")
            
            self.layer_list = LayerListWidget()
            self.layer_list.layer_selected.connect(self._on_layer_selected)
            self.layer_list.layers_reordered.connect(self._on_layers_reordered)
            left_tabs.addTab(self.layer_list, "Layers")
            
            left_layout.addWidget(left_tabs)
            splitter.addWidget(left_widget)
            
            # Center - Preview
            self.preview = PreviewWidget()
            splitter.addWidget(self.preview)
            
            # Right panel
            right_widget = QWidget()
            right_layout = QVBoxLayout(right_widget)
            
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            
            self.properties = PropertyPanel()
            self.properties.property_changed.connect(self._on_property_changed)
            scroll.setWidget(self.properties)
            
            right_layout.addWidget(scroll)
            
            # AI Generator
            ai_group = QGroupBox("AI Generator")
            ai_layout = QVBoxLayout(ai_group)
            
            self.ai_prompt = QLineEdit()
            self.ai_prompt.setPlaceholderText("e.g., 'cat with sunglasses'")
            ai_layout.addWidget(self.ai_prompt)
            
            ai_btn_layout = QHBoxLayout()
            self.ai_generate = QPushButton("Generate")
            self.ai_generate.clicked.connect(self._generate_ai)
            ai_btn_layout.addWidget(self.ai_generate)
            
            self.ai_style = QComboBox()
            self.ai_style.addItems(["default", "neon", "minimal", "detailed", "monochrome"])
            ai_btn_layout.addWidget(self.ai_style)
            ai_layout.addLayout(ai_btn_layout)
            
            right_layout.addWidget(ai_group)
            
            # Optimizer
            opt_group = QGroupBox("Optimizer")
            opt_layout = QVBoxLayout(opt_group)
            
            self.optimize_btn = QPushButton("Optimize Layers (→32)")
            self.optimize_btn.clicked.connect(self._optimize)
            opt_layout.addWidget(self.optimize_btn)
            
            right_layout.addWidget(opt_group)
            right_layout.addStretch()
            
            splitter.addWidget(right_widget)
            
            splitter.setSizes([300, 600, 350])
        
        def _setup_actions(self):
            self.act_new = QAction("New", self)
            self.act_new.setShortcut("Ctrl+N")
            self.act_new.triggered.connect(self._new_emblem)
            
            self.act_open = QAction("Open...", self)
            self.act_open.setShortcut("Ctrl+O")
            self.act_open.triggered.connect(self._open_emblem)
            
            self.act_save = QAction("Save", self)
            self.act_save.setShortcut("Ctrl+S")
            self.act_save.triggered.connect(self._save_emblem)
            
            self.act_save_as = QAction("Save As...", self)
            self.act_save_as.setShortcut("Ctrl+Shift+S")
            self.act_save_as.triggered.connect(self._save_emblem_as)
            
            self.act_import = QAction("Import Image...", self)
            self.act_import.setShortcut("Ctrl+I")
            self.act_import.triggered.connect(self._import_image)
            
            self.act_export = QAction("Export to Plutonium...", self)
            self.act_export.setShortcut("Ctrl+E")
            self.act_export.triggered.connect(self._export_plutonium)
            
            self.act_exit = QAction("Exit", self)
            self.act_exit.setShortcut("Ctrl+Q")
            self.act_exit.triggered.connect(self.close)
        
        def _setup_menu(self):
            menubar = self.menuBar()
            
            file_menu = menubar.addMenu("File")
            file_menu.addAction(self.act_new)
            file_menu.addAction(self.act_open)
            file_menu.addAction(self.act_save)
            file_menu.addAction(self.act_save_as)
            file_menu.addSeparator()
            file_menu.addAction(self.act_import)
            file_menu.addAction(self.act_export)
            file_menu.addSeparator()
            file_menu.addAction(self.act_exit)
            
            edit_menu = menubar.addMenu("Edit")
            
            tools_menu = menubar.addMenu("Tools")
            
            help_menu = menubar.addMenu("Help")
            about_action = QAction("About", self)
            about_action.triggered.connect(self._show_about)
            help_menu.addAction(about_action)
        
        def _setup_toolbar(self):
            toolbar = QToolBar("Main Toolbar")
            toolbar.setIconSize(QSize(24, 24))
            self.addToolBar(toolbar)
            
            toolbar.addAction(self.act_new)
            toolbar.addAction(self.act_open)
            toolbar.addAction(self.act_save)
            toolbar.addSeparator()
            toolbar.addAction(self.act_import)
            toolbar.addAction(self.act_export)
        
        def _setup_statusbar(self):
            self.statusBar().showMessage("Ready")
            self.layer_count_label = QLabel("Layers: 0")
            self.statusBar().addPermanentWidget(self.layer_count_label)
        
        def _update_ui(self):
            self.layer_list.set_layers(self.layers)
            self.preview.set_layers(self.layers)
            self.layer_count_label.setText(f"Layers: {len(self.layers)}")
            
            if self.current_file:
                self.setWindowTitle(f"BO2 Emblem Studio - {os.path.basename(self.current_file)}")
            else:
                self.setWindowTitle("BO2 Emblem Studio - Untitled")
        
        def _new_emblem(self):
            self.layers = []
            self.current_file = None
            self._update_ui()
            self.statusBar().showMessage("New emblem created")
        
        def _open_emblem(self):
            path, _ = QFileDialog.getOpenFileName(
                self, "Open Emblem", "", 
                "Emblem Files (*.emblem *.bin);;All Files (*.*)"
            )
            if path:
                try:
                    self.layers = EmblemParser.parse_file(path)
                    self.current_file = path
                    self._update_ui()
                    self.statusBar().showMessage(f"Loaded {path}")
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to load emblem:\n{e}")
        
        def _save_emblem(self):
            if self.current_file:
                self._save_to_file(self.current_file)
            else:
                self._save_emblem_as()
        
        def _save_emblem_as(self):
            path, _ = QFileDialog.getSaveFileName(
                self, "Save Emblem", "", 
                "Emblem Files (*.emblem);;Binary Files (*.bin);;All Files (*.*)"
            )
            if path:
                self._save_to_file(path)
        
        def _save_to_file(self, path: str):
            try:
                EmblemSerializer.write_file(path, self.layers)
                self.current_file = path
                self._update_ui()
                self.statusBar().showMessage(f"Saved to {path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save:\n{e}")
        
        def _import_image(self):
            path, _ = QFileDialog.getOpenFileName(
                self, "Import Image", "",
                "Images (*.png *.jpg *.jpeg *.webp *.bmp *.svg);;All Files (*.*)"
            )
            if path:
                try:
                    importer = ImageImporter()
                    layers = importer.import_image(path)
                    self.layers = layers
                    self._update_ui()
                    self.statusBar().showMessage(f"Imported {len(layers)} layers from {path}")
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to import image:\n{e}")
        
        def _export_plutonium(self):
            if not self.layers:
                QMessageBox.warning(self, "Warning", "No layers to export")
                return
            
            slot, ok = QInputDialog.getInt(
                self, "Export to Plutonium", 
                "Enter slot number (1-20):", 1, 1, 20
            )
            if ok:
                try:
                    exporter = EmblemExporter()
                    exporter.export_to_plutonium(self.layers, slot)
                    self.statusBar().showMessage(f"Exported to Plutonium slot {slot}")
                    QMessageBox.information(self, "Success", 
                        f"Emblem exported to Plutonium slot {slot}\nRestart game to see changes.")
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to export:\n{e}")
        
        def _on_shape_selected(self, shape_id: int):
            if self.layers:
                next_index = max(l.index for l in self.layers) + 1
            else:
                next_index = 0
            
            layer = EmblemLayer(
                index=next_index,
                shape_id=shape_id,
                r=1.0, g=1.0, b=1.0, a=1.0,
                pos_x=0.0, pos_y=0.0,
                scale_x=0.0, scale_y=0.0,
                rotation=0.0
            )
            self.layers.append(layer)
            self._update_ui()
        
        def _on_layer_selected(self, index: int):
            if 0 <= index < len(self.layers):
                self.properties.set_layer(self.layers[index])
        
        def _on_layers_reordered(self):
            for i, layer in enumerate(self.layers):
                layer.index = i
            self._update_ui()
        
        def _on_property_changed(self, layer_index: int, prop: str, value):
            if 0 <= layer_index < len(self.layers):
                layer = self.layers[layer_index]
                
                if prop == "shape_id":
                    layer.shape_id = value
                elif prop == "color":
                    layer.r, layer.g, layer.b, layer.a = value
                elif prop == "pos_x":
                    layer.pos_x = value
                elif prop == "pos_y":
                    layer.pos_y = value
                elif prop == "scale_x":
                    layer.scale_x = value
                elif prop == "scale_y":
                    layer.scale_y = value
                elif prop == "rotation":
                    layer.rotation = value
                elif prop == "outlined":
                    layer.outlined = value
                elif prop == "flipped":
                    layer.flipped = value
                
                self._update_ui()
        
        def _generate_ai(self):
            prompt = self.ai_prompt.text().strip()
            if not prompt:
                return
            
            try:
                style = self.ai_style.currentText()
                generator = EmblemAIGenerator()
                layers = generator.generate_complex(prompt, style)
                self.layers = layers
                self._update_ui()
                self.statusBar().showMessage(f"Generated '{prompt}' with {len(layers)} layers")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"AI generation failed:\n{e}")
        
        def _optimize(self):
            if not self.layers:
                return
            
            try:
                optimizer = EmblemOptimizer(OptimizerConfig(target_layers=32))
                self.layers = optimizer.optimize(self.layers)
                self._update_ui()
                self.statusBar().showMessage(f"Optimized to {len(self.layers)} layers")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Optimization failed:\n{e}")
        
        def _show_about(self):
            QMessageBox.about(self, "About BO2 Emblem Studio",
                "BO2 Emblem Studio v1.0\n\n"
                "Complete toolkit for Call of Duty: Black Ops II / Plutonium T6\n"
                "emblem editing, creation, and conversion.\n\n"
                "Features:\n"
                "• Full .emblem/.bin parser & serializer\n"
                "• Pixel-perfect renderer with 260+ reference shapes\n"
                "• Image → emblem converter (PNG, JPG, WebP, BMP, SVG)\n"
                "• Layer optimizer (32-layer limit)\n"
                "• AI text-to-emblem generator\n"
                "• Plutonium T6 auto-exporter\n"
                "• Modern PySide6 GUI editor\n\n"
                "Based on reverse engineering by:\n"
                "• 505e06b2 (Black-Ops-2-Emblem-Editor)\n"
                "• alexkotr1 (bo2-emblem-toolkit)\n"
                "• olie304 (CallOfDutyEmblemSpecs)"
            )


    def main():
        """Entry point for GUI application."""
        app = QApplication(sys.argv)
        app.setStyle("Fusion")
        
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(30, 30, 30))
        palette.setColor(QPalette.WindowText, Qt.white)
        palette.setColor(QPalette.Base, QColor(20, 20, 20))
        palette.setColor(QPalette.AlternateBase, QColor(40, 40, 40))
        palette.setColor(QPalette.ToolTipBase, Qt.white)
        palette.setColor(QPalette.ToolTipText, Qt.white)
        palette.setColor(QPalette.Text, Qt.white)
        palette.setColor(QPalette.Button, QColor(45, 45, 45))
        palette.setColor(QPalette.ButtonText, Qt.white)
        palette.setColor(QPalette.BrightText, Qt.red)
        palette.setColor(QPalette.Link, QColor(42, 130, 218))
        palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
        palette.setColor(QPalette.HighlightedText, Qt.black)
        app.setPalette(palette)
        
        window = EmblemEditor()
        window.show()
        sys.exit(app.exec())


else:
    def main():
        print("PySide6 not installed. Install with: pip install PySide6")


if __name__ == "__main__":
    main()
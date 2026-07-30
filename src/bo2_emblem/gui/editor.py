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
        QInputDialog, QGraphicsView, QGraphicsScene, QGraphicsPixmapItem
    )
    from PySide6.QtCore import Qt, QSize, QRect, Signal, Slot, QTimer
    from PySide6.QtGui import (
        QPixmap, QImage, QPainter, QColor, QPen, QBrush, QFont,
        QAction, QIcon, QPalette, QWheelEvent, QMouseEvent,
        QStandardItemModel, QStandardItem
    )
    HAS_PYSIDE6 = True
except ImportError:
    HAS_PYSIDE6 = False
    # Create dummy classes for type hints
    class QObject: pass
    class QWidget: pass
    class Signal: pass

# Use absolute imports instead of relative imports
from bo2_emblem.parser import EmblemLayer, EmblemParser
from bo2_emblem.serializer import EmblemSerializer
from bo2_emblem.renderer import EmblemRenderer
from bo2_emblem.importer import ImageImporter, ImportConfig
from bo2_emblem.exporter import EmblemExporter, ExportConfig
from bo2_emblem.optimizer import EmblemOptimizer, OptimizerConfig
from bo2_emblem.ai import EmblemAIGenerator
from bo2_emblem.shape_map import (
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
            self.setHeaderLabels(["Layer", "Shape", "Color", "Pos", "Scale", "Rot", "O", "F"])
            self.setColumnWidth(0, 60)
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
            shape_name = get_shape_name(layer.shape_id).split("/", 1)[-1]
            color_str = f"#{int(layer.r*255):02X}{int(layer.g*255):02X}{int(layer.b*255):02X}"
            pos_str = f"{layer.pos_x:.2f}, {layer.pos_y:.2f}"
            scale_str = f"{layer.true_scale_x:.2f}, {layer.true_scale_y:.2f}"
            
            # Display Layer number 1-32
            layer_num = layer.index + 1 
            
            item = QTreeWidgetItem([
                f"Layer {layer_num}",
                shape_name,
                color_str,
                pos_str,
                scale_str,
                f"{layer.rotation:.1f}°",
                "✓" if layer.outlined else "",
                "✓" if layer.flipped else ""
            ])
            item.setData(0, Qt.UserRole, layer.index)
            
            # Better alternating colors for Dark Theme
            if layer.index % 2 == 0:
                for col in range(self.columnCount()):
                    item.setBackground(col, QColor(40, 40, 40))
            else:
                for col in range(self.columnCount()):
                    item.setBackground(col, QColor(32, 32, 32))
            
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


    class PreviewWidget(QGraphicsView):
        """Widget for previewing the rendered emblem with zoom and pan."""
        
        def __init__(self):
            super().__init__()
            self.scene = QGraphicsScene(self)
            self.setScene(self.scene)
            self.setMinimumSize(512, 512)
            self.setStyleSheet("background-color: #181818; border: 1px solid #444;")
            
            self.setRenderHint(QPainter.SmoothPixmapTransform)
            self.setRenderHint(QPainter.Antialiasing)
            self.setDragMode(QGraphicsView.ScrollHandDrag)
            
            self.layers = []
            self.renderer = EmblemRenderer()
            self.pixmap_item = None
            self.bg_rect = None
            self.bg_dark = True
        
        def set_layers(self, layers: List[EmblemLayer]):
            self.layers = layers
            self._render()
            
        def toggle_background(self):
            self.bg_dark = not self.bg_dark
            self._render()
        
        def _render(self):
            if not self.layers:
                self.scene.clear()
                self.pixmap_item = None
                self.bg_rect = None
                return
            
            base_size = 1024
            
            # If light bg is selected, render light
            bg_render = (200, 200, 200, 255) if not self.bg_dark else (0, 0, 0, 0)
            
            img = self.renderer.render_png(self.layers, size=base_size, bg_color=bg_render)
            img_data = img.tobytes("raw", "RGBA")
            qimg = QImage(img_data, img.width, img.height, QImage.Format_RGBA8888)
            pixmap = QPixmap.fromImage(qimg)
            
            if self.pixmap_item is None:
                self.scene.clear()
                bg_col = QColor(30, 30, 30) if self.bg_dark else QColor(200, 200, 200)
                self.bg_rect = self.scene.addRect(0, 0, base_size, base_size, QPen(QColor(80, 80, 80)), QBrush(bg_col))
                self.pixmap_item = self.scene.addPixmap(pixmap)
            else:
                bg_col = QColor(30, 30, 30) if self.bg_dark else QColor(200, 200, 200)
                self.bg_rect.setBrush(QBrush(bg_col))
                self.pixmap_item.setPixmap(pixmap)
                
            self.scene.setSceneRect(self.bg_rect.boundingRect())
            
        def wheelEvent(self, event: QWheelEvent):
            if event.modifiers() == Qt.ControlModifier:
                delta = event.angleDelta().y()
                if delta > 0:
                    self.scale(1.1, 1.1)
                elif delta < 0:
                    self.scale(0.9, 0.9)
                event.accept()
            else:
                super().wheelEvent(event)


    class EmblemEditor(QMainWindow):
        emblem_updated = Signal()
        emblem_saved = Signal(str)
        ai_log_signal = Signal(str)
        ai_test_success_signal = Signal(str, str)
        ai_test_error_signal = Signal(str, str)
        ai_generation_complete_signal = Signal(list)
        ai_generation_failed_signal = Signal(str)

        def __init__(self):
            super().__init__()
            self.setWindowTitle("BO2 Emblem Studio")
            self.resize(1400, 900)
            
            self.layers = []
            self.current_file = None
            self.undo_stack = []
            self.redo_stack = []
            self.clipboard_layer = None
            
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
            
            # Left panel - Shapes and Layers
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
            
            # Right panel - Properties
            right_widget = QWidget()
            right_layout = QVBoxLayout(right_widget)
            
            # Use tabs for right panel
            self.right_tabs = QTabWidget()
            
            # Properties tab
            props_widget = QWidget()
            props_layout = QVBoxLayout(props_widget)
            
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            
            self.properties = PropertyPanel()
            self.properties.property_changed.connect(self._on_property_changed)
            scroll.setWidget(self.properties)
            
            props_layout.addWidget(scroll)
            self.right_tabs.addTab(scroll, "Properties")
            
            # AI Studio tab
            ai_studio_widget = self._create_ai_studio_tab()
            self.right_tabs.addTab(ai_studio_widget, "AI Studio")
            
            # Optimizer tab
            opt_widget = QWidget()
            opt_layout = QVBoxLayout(opt_widget)
            
            opt_group = QGroupBox("Optimizer")
            opt_layout = QVBoxLayout(opt_group)
            
            self.optimize_btn = QPushButton("Optimize Layers (→32)")
            self.optimize_btn.clicked.connect(self._optimize)
            opt_layout.addWidget(self.optimize_btn)
            
            opt_layout.addWidget(opt_group)
            opt_layout.addStretch()
            
            self.right_tabs.addTab(opt_widget, "Optimizer")
            
            right_layout.addWidget(self.right_tabs)
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
            
            # Edit Actions
            self.act_undo = QAction("Undo", self)
            self.act_undo.setShortcut("Ctrl+Z")
            self.act_undo.triggered.connect(self._undo)
            self.act_undo.setEnabled(False)
            
            self.act_redo = QAction("Redo", self)
            self.act_redo.setShortcut("Ctrl+Y")
            self.act_redo.triggered.connect(self._redo)
            self.act_redo.setEnabled(False)
            
            self.act_copy = QAction("Copy Layer", self)
            self.act_copy.setShortcut("Ctrl+C")
            self.act_copy.triggered.connect(self._copy_layer)
            
            self.act_paste = QAction("Paste Layer", self)
            self.act_paste.setShortcut("Ctrl+V")
            self.act_paste.triggered.connect(self._paste_layer)
            
            self.act_delete = QAction("Delete Layer", self)
            self.act_delete.setShortcut("Del")
            self.act_delete.triggered.connect(self._delete_layer)
            
            self.act_clear = QAction("Clear All", self)
            self.act_clear.triggered.connect(self._clear_layers)
            
            self.act_move_up = QAction("Move Layer Up", self)
            self.act_move_up.setShortcut("Ctrl+Up")
            self.act_move_up.triggered.connect(self._move_layer_up)
            
            self.act_move_down = QAction("Move Layer Down", self)
            self.act_move_down.setShortcut("Ctrl+Down")
            self.act_move_down.triggered.connect(self._move_layer_down)
            
            # Tools Actions
            self.act_tool_ai = QAction("AI Emblem Generator", self)
            self.act_tool_ai.triggered.connect(lambda: self.right_tabs.setCurrentIndex(1))
            
            self.act_tool_opt = QAction("Layer Optimizer", self)
            self.act_tool_opt.triggered.connect(lambda: self.right_tabs.setCurrentIndex(2))
            
            self.act_tool_bg = QAction("Toggle Preview Background", self)
            self.act_tool_bg.triggered.connect(self.preview.toggle_background)
        
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
            edit_menu.addAction(self.act_undo)
            edit_menu.addAction(self.act_redo)
            edit_menu.addSeparator()
            edit_menu.addAction(self.act_copy)
            edit_menu.addAction(self.act_paste)
            edit_menu.addAction(self.act_delete)
            edit_menu.addSeparator()
            edit_menu.addAction(self.act_move_up)
            edit_menu.addAction(self.act_move_down)
            edit_menu.addSeparator()
            edit_menu.addAction(self.act_clear)
            
            tools_menu = menubar.addMenu("Tools")
            tools_menu.addAction(self.act_tool_ai)
            tools_menu.addAction(self.act_tool_opt)
            tools_menu.addSeparator()
            tools_menu.addAction(self.act_tool_bg)
            
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
            import traceback
            import logging
            logger = logging.getLogger("EmblemEditor")
            
            path, _ = QFileDialog.getOpenFileName(
                self, "Open Emblem", "", 
                "Emblem Files (*.emblem *.bin);;All Files (*.*)"
            )
            if path:
                if not os.path.exists(path):
                    QMessageBox.critical(self, "Error", "Arquivo não encontrado")
                    return
                
                logger.info(f"Tentando abrir: {path}")
                logger.info(f"Tamanho: {os.path.getsize(path)} bytes")
                
                try:
                    layers, header = EmblemParser.parse_file(path)
                    logger.info("Parser bem sucedido")
                    logger.info(f"Layers: {len(layers)}")
                    
                    self.layers = layers
                    self.current_file = path
                    self._update_ui()
                    self.statusBar().showMessage(f"Loaded {path}")
                except Exception as e:
                    logger.error(f"Parser falhou: {e}")
                    logger.error(traceback.format_exc())
                    
                    logger.info("Tentando fallback leitura byte-a-byte direta...")
                    try:
                        with open(path, "rb") as f:
                            data = f.read()
                        self.layers = EmblemParser.parse_bytes(data)
                        self.current_file = path
                        self._update_ui()
                        self.statusBar().showMessage(f"Loaded {path} via fallback")
                    except Exception as fallback_e:
                        QMessageBox.critical(self, "Error", f"Failed to load emblem:\n{e}\nFallback failed: {fallback_e}")
                        logger.error(traceback.format_exc())
        
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
                    self.layers = layers[:32]
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
            if len(self.layers) >= 32:
                QMessageBox.warning(self, "Layer Limit", "Maximum of 32 layers reached.")
                return
                
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

        # ===================== AI STUDIO TAB =====================

        def _create_ai_studio_tab(self):
            """Create the AI Studio tab with Hermes integration."""
            widget = QWidget()
            layout = QVBoxLayout(widget)

            # AI Connection Settings
            conn_group = QGroupBox("AI Connection")
            conn_layout = QFormLayout(conn_group)

            self.ai_provider = QComboBox()
            self.ai_provider.addItems([
                "Local (Hermes Agent)",
                "OpenAI",
                "Anthropic (Claude)",
                "Google (Gemini)",
                "NVIDIA",
                "OpenRouter",
                "Ollama",
                "LM Studio",
                "vLLM",
                "Custom (OpenAI Compatible)"
            ])
            conn_layout.addRow("Provider:", self.ai_provider)

            self.ai_endpoint = QLineEdit()
            self.ai_endpoint.setPlaceholderText("e.g., http://localhost:8080/v1")
            conn_layout.addRow("Endpoint:", self.ai_endpoint)

            self.ai_model = QLineEdit()
            self.ai_model.setPlaceholderText("e.g., nemotron-3-ultra, gpt-4, claude-3-opus")
            conn_layout.addRow("Model:", self.ai_model)

            self.ai_api_key = QLineEdit()
            self.ai_api_key.setEchoMode(QLineEdit.Password)
            self.ai_api_key.setPlaceholderText("API Key (if required)")
            conn_layout.addRow("API Key:", self.ai_api_key)

            self.ai_test_conn = QPushButton("Test Connection")
            self.ai_test_conn.clicked.connect(self._test_ai_connection)
            conn_layout.addRow("", self.ai_test_conn)

            layout.addWidget(conn_group)

            # Prompt Input
            prompt_group = QGroupBox("Prompt")
            prompt_layout = QVBoxLayout(prompt_group)

            self.ai_prompt = QTextEdit()
            self.ai_prompt.setPlaceholderText(
                "Describe the emblem you want...\n\n"
                "Examples:\n"
                "• \"Realistic skull with glowing blue eyes, zombie style\"\n"
                "• \"Tactical gas mask with glowing green lenses, tactical\"\n"
                "• \"Eagle with spread wings, patriotic colors\"\n"
                "• \"Cyberpunk dragon with neon blue scales, glowing eyes\"\n"
                "• \"Vintage pin-up girl, 1940s nose art style\"\n"
                "• \"Atomic bomb mushroom cloud, retro warning sign style\""
            )
            self.ai_prompt.setMaximumHeight(150)
            prompt_layout.addWidget(self.ai_prompt)

            # Style and options
            options_layout = QHBoxLayout()

            self.ai_style = QComboBox()
            self.ai_style.addItems(["default", "neon", "minimal", "detailed", "monochrome", "retro", "realistic"])
            options_layout.addWidget(QLabel("Style:"))
            options_layout.addWidget(self.ai_style)

            self.ai_symmetry = QComboBox()
            self.ai_symmetry.addItems(["bilateral", "radial", "asymmetric"])
            options_layout.addWidget(QLabel("Symmetry:"))
            options_layout.addWidget(self.ai_symmetry)

            self.ai_complexity = QSpinBox()
            self.ai_complexity.setRange(1, 5)
            self.ai_complexity.setValue(3)
            options_layout.addWidget(QLabel("Complexity:"))
            options_layout.addWidget(self.ai_complexity)

            self.ai_max_layers = QSpinBox()
            self.ai_max_layers.setRange(1, 32)
            self.ai_max_layers.setValue(32)
            options_layout.addWidget(QLabel("Max Layers:"))
            options_layout.addWidget(self.ai_max_layers)

            prompt_layout.addLayout(options_layout)

            # Buttons
            btn_layout = QHBoxLayout()
            self.ai_generate = QPushButton("Generate Emblem")
            self.ai_generate.clicked.connect(self._generate_ai_hermes)
            self.ai_generate.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; font-weight: bold; padding: 8px; }")
            btn_layout.addWidget(self.ai_generate)

            self.ai_refine = QPushButton("Refine")
            self.ai_refine.clicked.connect(self._refine_ai)
            self.ai_refine.setEnabled(False)
            btn_layout.addWidget(self.ai_refine)

            self.ai_recreate = QPushButton("Recreate")
            self.ai_recreate.clicked.connect(self._recreate_ai)
            self.ai_recreate.setEnabled(False)
            btn_layout.addWidget(self.ai_recreate)

            self.ai_improve = QPushButton("Improve")
            self.ai_improve.clicked.connect(self._improve_ai)
            self.ai_improve.setEnabled(False)
            btn_layout.addWidget(self.ai_improve)

            prompt_layout.addLayout(btn_layout)

            layout.addWidget(prompt_group)

            # Preview area for AI
            preview_group = QGroupBox("AI Preview")
            preview_layout = QVBoxLayout(preview_group)

            self.ai_preview = PreviewWidget()
            self.ai_preview.setMinimumSize(256, 256)
            preview_layout.addWidget(self.ai_preview)

            layout.addWidget(preview_group)

            # Log/Console
            log_group = QGroupBox("Log")
            log_layout = QVBoxLayout(log_group)

            self.ai_log = QTextEdit()
            self.ai_log.setReadOnly(True)
            self.ai_log.setMaximumHeight(100)
            self.ai_log.setFont(QFont("Consolas", 9))
            log_layout.addWidget(self.ai_log)

            layout.addWidget(log_group)

            return widget

        def _log_ai(self, message: str):
            """Log message to AI console."""
            from datetime import datetime
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.ai_log.append(f"[{timestamp}] {message}")
            self.ai_log.ensureCursorVisible()

        def _test_ai_connection(self):
            provider_text = self.ai_provider.currentText()
            endpoint = self.ai_endpoint.text().strip()
            model = self.ai_model.text().strip()
            api_key = self.ai_api_key.text().strip()

            if not endpoint:
                QMessageBox.warning(self, "Error", "Please enter an endpoint URL")
                return

            self._log_ai(f"Testing connection to {provider_text} at {endpoint}...")

            import requests
            # Run in thread to avoid blocking UI
            from threading import Thread
            def test():
                try:
                    headers = {"Content-Type": "application/json"}
                    if api_key:
                        headers["Authorization"] = f"Bearer {api_key}"

                    payload = {
                        "model": model or "default",
                        "messages": [{"role": "user", "content": "Test connection"}],
                        "max_tokens": 10
                    }

                    base = endpoint.rstrip('/')
                    if base.endswith('/api/v1') or base.endswith('/v1') or base.endswith('/messages'):
                        test_url = f"{base}/chat/completions"
                        if base.endswith('/messages'):
                            test_url = base
                    else:
                        if provider_text == "OpenRouter":
                            test_url = f"{base}/api/v1/chat/completions"
                        elif provider_text == "Anthropic (Claude)":
                            test_url = f"{base}/v1/messages"
                        else:
                            test_url = f"{base}/v1/chat/completions"

                    resp = requests.post(
                        test_url,
                        json=payload,
                        headers=headers,
                        timeout=10
                    )

                    if resp.status_code == 200:
                        self.ai_log_signal.emit("✅ Connection successful!")
                        self.ai_test_success_signal.emit(provider_text, "Connected successfully!")
                    else:
                        self.ai_log_signal.emit(f"❌ Connection failed: {resp.status_code} - {resp.text}")
                        self.ai_test_error_signal.emit(str(resp.status_code), resp.text)
                except Exception as e:
                    self.ai_log_signal.emit(f"❌ Error: {str(e)}")
                    self.ai_test_error_signal.emit("Exception", str(e))

            Thread(target=test).start()

        def _test_success(self, provider_text: str, msg: str):
            QMessageBox.information(self, "Success", f"Connected to {provider_text} successfully!\n{msg}")

        def _test_error(self, code: str, msg: str):
            QMessageBox.critical(self, "Error", f"Connection test failed ({code}):\n{msg}")

        def _generate_ai_hermes(self):
            """Generate emblem using Hermes AI."""
            prompt = self.ai_prompt.toPlainText().strip()
            if not prompt:
                QMessageBox.warning(self, "Warning", "Please enter a prompt")
                return

            self.ai_generate.setEnabled(False)
            self.ai_generate.setText("Generating...")
            self.ai_refine.setEnabled(False)
            self.ai_recreate.setEnabled(False)
            self.ai_improve.setEnabled(False)
            self._log_ai(f"Generating: {prompt[:50]}...")

            # Extract UI values on main thread!
            provider_text = self.ai_provider.currentText()
            endpoint = self.ai_endpoint.text().strip() or "http://localhost:8080/v1"
            api_key = self.ai_api_key.text().strip()
            model = self.ai_model.text().strip() or "nemotron-3-ultra"
            style = self.ai_style.currentText()
            symmetry = self.ai_symmetry.currentText()
            complexity = self.ai_complexity.value()

            import asyncio
            from bo2_emblem.ai_hermes import (
                EmblemConcept, HermesConfig, AIProvider, generate_emblem_async
            )
            from bo2_emblem.parser import EmblemLayer
            from threading import Thread

            def generate():
                try:

                    # Map provider
                    provider_map = {
                        "Local (Hermes Agent)": AIProvider.LOCAL,
                        "OpenAI": AIProvider.OPENAI,
                        "Anthropic (Claude)": AIProvider.ANTHROPIC,
                        "Google (Gemini)": AIProvider.GOOGLE,
                        "NVIDIA": AIProvider.NVIDIA,
                        "OpenRouter": AIProvider.OPENROUTER,
                        "Ollama": AIProvider.OLLAMA,
                        "LM Studio": AIProvider.LM_STUDIO,
                        "vLLM": AIProvider.VLLM,
                        "Custom (OpenAI Compatible)": AIProvider.CUSTOM,
                    }

                    provider = provider_map.get(provider_text, AIProvider.LOCAL)

                    config = HermesConfig(
                        provider=provider,
                        endpoint=endpoint,
                        api_key=api_key,
                        model=model,
                        temperature=0.7,
                        max_tokens=4096
                    )

                    concept = EmblemConcept(
                        name="AI Generated",
                        description=prompt,
                        style=style,
                        symmetry=symmetry,
                        complexity=complexity,
                        elements=[],
                        color_scheme="auto",
                        composition_notes=""
                    )

                    # Run async generation
                    import asyncio
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    from bo2_emblem.ai_hermes import generate_emblem_async
                    plan = loop.run_until_complete(
                        generate_emblem_async(concept, config)
                    )

                    # Convert plan to layers
                    layers = []
                    for i, layer_data in enumerate(plan.layers):
                        layer = EmblemLayer(
                            index=layer_data.get("index", i),
                            shape_id=layer_data.get("shape_id", 192),
                            r=layer_data.get("r", 1.0),
                            g=layer_data.get("g", 1.0),
                            b=layer_data.get("b", 1.0),
                            a=layer_data.get("a", 1.0),
                            pos_x=layer_data.get("pos_x", 0.0),
                            pos_y=layer_data.get("pos_y", 0.0),
                            scale_x=layer_data.get("scale_x", 0.0),
                            scale_y=layer_data.get("scale_y", 0.0),
                            rotation=layer_data.get("rotation", 0.0),
                            outlined=layer_data.get("outlined", False),
                            flipped=layer_data.get("flipped", False)
                        )
                        layers.append(layer)

                    # Update UI on main thread safely
                    self.ai_generation_complete_signal.emit(layers)
                    
                except Exception as e:
                    self.ai_log_signal.emit(f"❌ Generation failed: {str(e)}")
                    self.ai_generation_failed_signal.emit(str(e))

            Thread(target=generate).start()

        def _apply_generated_layers(self, layers: list):
            """Apply generated layers to editor (called on main thread)."""
            self.layers = layers
            self._update_ui()
            self._log_ai(f"✅ Generated {len(layers)} layers successfully!")
            self.ai_refine.setEnabled(True)
            self.ai_recreate.setEnabled(True)
            self.ai_improve.setEnabled(True)
            self.ai_generate.setEnabled(True)
            self.ai_generate.setText("Generate Emblem")

            # Render preview
            self.ai_preview.set_layers(layers)

        def _generation_failed(self, error: str):
            self.ai_generate.setEnabled(True)
            self.ai_generate.setText("Generate Emblem")
            QMessageBox.critical(self, "Generation Failed", error)

        def _refine_ai(self):
            """Refine the current generation with feedback."""
            feedback, ok = QInputDialog.getText(self, "Refine", "What would you like to change?")
            if ok and feedback:
                self._log_ai(f"Refining: {feedback}")
                # TODO: Implement refinement with feedback

        def _recreate_ai(self):
            """Recreate with same prompt but different seed."""
            self._log_ai("Recreating with new variation...")
            self._generate_ai_hermes()

        def _improve_ai(self):
            """Auto-improve the current generation."""
            self._log_ai("Auto-improving...")
            # TODO: Implement auto-improvement

        def _save_state_for_undo(self):
            import copy
            self.undo_stack.append(copy.deepcopy(self.layers))
            if len(self.undo_stack) > 50:
                self.undo_stack.pop(0)
            self.redo_stack.clear()
            self.act_undo.setEnabled(True)
            self.act_redo.setEnabled(False)

        def _undo(self):
            if not self.undo_stack:
                return
            import copy
            self.redo_stack.append(copy.deepcopy(self.layers))
            self.layers = self.undo_stack.pop()
            self._update_ui()
            self.act_undo.setEnabled(len(self.undo_stack) > 0)
            self.act_redo.setEnabled(True)

        def _redo(self):
            if not self.redo_stack:
                return
            import copy
            self.undo_stack.append(copy.deepcopy(self.layers))
            self.layers = self.redo_stack.pop()
            self._update_ui()
            self.act_undo.setEnabled(True)
            self.act_redo.setEnabled(len(self.redo_stack) > 0)

        def _copy_layer(self):
            selected = self.layer_list.selectedItems()
            if not selected:
                return
            idx = self.layer_list.indexOfTopLevelItem(selected[0])
            import copy
            self.clipboard_layer = copy.deepcopy(self.layers[idx])
            self.statusBar().showMessage("Layer copied to clipboard")

        def _paste_layer(self):
            if not self.clipboard_layer:
                self.statusBar().showMessage("Clipboard is empty")
                return
            if len(self.layers) >= 32:
                QMessageBox.warning(self, "Layer Limit", "Maximum of 32 layers reached.")
                return
            self._save_state_for_undo()
            
            selected = self.layer_list.selectedItems()
            import copy
            new_layer = copy.deepcopy(self.clipboard_layer)
            
            if selected:
                idx = self.layer_list.indexOfTopLevelItem(selected[0])
                self.layers.insert(idx, new_layer)
            else:
                self.layers.append(new_layer)
                
            for i, l in enumerate(self.layers):
                l.index = i
                
            self._update_ui()
            self.statusBar().showMessage("Layer pasted")

        def _delete_layer(self):
            selected = self.layer_list.selectedItems()
            if not selected:
                return
            self._save_state_for_undo()
            idx = self.layer_list.indexOfTopLevelItem(selected[0])
            self.layers.pop(idx)
            for i, l in enumerate(self.layers):
                l.index = i
            self._update_ui()

        def _clear_layers(self):
            if not self.layers: return
            self._save_state_for_undo()
            self.layers = []
            self._update_ui()

        def _move_layer_up(self):
            selected = self.layer_list.selectedItems()
            if not selected: return
            idx = self.layer_list.indexOfTopLevelItem(selected[0])
            if idx == 0: return
            self._save_state_for_undo()
            self.layers[idx], self.layers[idx-1] = self.layers[idx-1], self.layers[idx]
            for i, l in enumerate(self.layers): l.index = i
            self._update_ui()
            self.layer_list.setCurrentItem(self.layer_list.topLevelItem(idx-1))

        def _move_layer_down(self):
            selected = self.layer_list.selectedItems()
            if not selected: return
            idx = self.layer_list.indexOfTopLevelItem(selected[0])
            if idx == len(self.layers) - 1: return
            self._save_state_for_undo()
            self.layers[idx], self.layers[idx+1] = self.layers[idx+1], self.layers[idx]
            for i, l in enumerate(self.layers): l.index = i
            self._update_ui()
            self.layer_list.setCurrentItem(self.layer_list.topLevelItem(idx+1))

else:
    def main():
        print("PySide6 not installed. Install with: pip install PySide6")


def main():
    """Entry point for GUI application."""
    if not HAS_PYSIDE6:
        print("PySide6 not installed. Install with: pip install PySide6")
        return
    
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


if __name__ == "__main__":
    import sys
    import traceback
    
    def log_uncaught_exceptions(ex_cls, ex, tb):
        with open("crash_log.txt", "a") as f:
            f.write("".join(traceback.format_tb(tb)))
            f.write(f"{ex_cls.__name__}: {ex}\n")
        sys.__excepthook__(ex_cls, ex, tb)
        
    sys.excepthook = log_uncaught_exceptions
    main()
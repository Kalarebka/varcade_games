import Phaser from 'phaser'

import { audioManager } from '../audio_manager.js'
import { getModalLayoutData} from '../game_data/layout.js'

import { TextButton } from './text_button'
import { IconButton } from './icon_button'

import {getSaveGameData, writeSaveGameData} from "../game_data/save_data"

function showErrorModal (scene, title, messageText, buttonText) {
  const modalLayoutData = getModalLayoutData('Error').window
  const errorWindow = scene.add.zone(
    modalLayoutData.x,
    modalLayoutData.y,
    modalLayoutData.w,
    modalLayoutData.h
  )

  const errorModal = new ErrorModal(errorWindow, title, messageText, buttonText)

  if (scene.scene.get('Error')) {
    console.log('[MODAL] !! Not adding a modal as there is one already active.')
    return
  }
  scene.scene.add('Error', errorModal, true)
}

function showSettingsModal (scene) {
  const modalLayoutData = getModalLayoutData('Settings').window
  const settingsWindow = scene.add.zone(
    modalLayoutData.x,
    modalLayoutData.y,
    modalLayoutData.w,
    modalLayoutData.h
  )
  const settingsModal = new SettingsModal(settingsWindow);

  if (scene.scene.get('Settings')) {
    console.log('[MODAL] !! Not adding a modal as there is one already active.');
    return;
  }
  scene.scene.add('Settings', settingsModal, true);
}

class ErrorModal extends Phaser.Scene {
  constructor (parent, title, messageText, buttonText, onClose) {
    super('Error')
    this.parent = parent
    this.layoutData = getModalLayoutData('Error')
    this.title = title
    this.messageText = messageText
    this.buttonText = buttonText
  }

  create () {
    const headerLayout = this.layoutData.ui.header

    this.add.bitmapText(
      headerLayout.x,
      headerLayout.y,
      headerLayout.bitmapFontId,
      this.title,
      headerLayout.fontSize
    ).setOrigin(
      headerLayout.originX,
      headerLayout.originY
    ).setDepth(
      200
    ).setTint(
      headerLayout.color
    )

    const messageLayout = this.layoutData.ui.message

    this.add.bitmapText(
      messageLayout.x,
      messageLayout.y,
      messageLayout.bitmapFontId,
      this.messageText,
      messageLayout.fontSize
    ).setOrigin(
      messageLayout.originX,
      messageLayout.originY
    ).setDepth(
      200
    ).setTint(
      messageLayout.color
    ).setMaxWidth(
      messageLayout.maxWidth
    )

    const closeButtonLayout = this.layoutData.ui.closeButton
    this.fightButton = new TextButton(
      this,
      closeButtonLayout.x,
      closeButtonLayout.y,
      this.buttonText,
      closeButtonLayout.bitmapFontId,
      closeButtonLayout.fontSize,
      closeButtonLayout.color,
      () => {
        this.parent.destroy()
        this.scene.remove()
      }
    ).setOrigin(
      closeButtonLayout.originX,
      closeButtonLayout.originY
    )
    this.add.existing(this.fightButton)

    this.cameras.main.setBackgroundColor(0x000000)
    this.cameras.main.setViewport(this.parent.x, this.parent.y, 480, 320)
  }
}

class SettingsModal extends Phaser.Scene {
  constructor (parent, onClose) {
    super('Settings')
    this.parent = parent
    this.layoutData = getModalLayoutData('Settings')
    this.title = "Settings"
    this.buttonText = "Exit"
  }

  init (data) {
    this.saveGameData = getSaveGameData()
  }

  create ()  {
    const headerLayout = this.layoutData.ui.header

    this.add.bitmapText(
      headerLayout.x,
      headerLayout.y,
      headerLayout.bitmapFontId,
      this.title,
      headerLayout.fontSize
    ).setOrigin(
      headerLayout.originX,
      headerLayout.originY
    ).setDepth(
      200
    ).setTint(
      headerLayout.color
    )

    /**
      Add settings options buttons
    **/
    
    const settingsLayout = this.layoutData.ui.settingsList
       
    const activeMusicIcon = audioManager.musicEnabled
      ? settingsLayout.icons.soundOnIcon
      : settingsLayout.icons.soundOffIcon
    const inactiveMusicIcon = audioManager.musicEnabled
      ? settingsLayout.icons.soundOffIcon
      : settingsLayout.icons.soundOnIcon

    const activeEffectsIcon = audioManager.effectsEnabled
      ? settingsLayout.icons.effectsOnIcon
      : settingsLayout.icons.effectsOffIcon
    const inactiveEffectsIcon = audioManager.effectsEnabled
      ? settingsLayout.icons.effectsOffIcon
      : settingsLayout.icons.effectsOnIcon

    this.add.existing(new IconButton(this,
      settingsLayout.x, settingsLayout.y, 'global_texture',
      activeMusicIcon, inactiveMusicIcon, 0xFFFFFF, () => {
        audioManager.toggleMusicEnabled();
        this.saveGameData.musicEnabled = !this.saveGameData.musicEnabled;
      }).setOrigin(settingsLayout.originX, settingsLayout.originY))

    this.add.existing(new IconButton(this,
      settingsLayout.x, settingsLayout.y + settingsLayout.padding, 'global_texture',
      activeEffectsIcon, inactiveEffectsIcon, 0xFFFFFF, () => {
        audioManager.toggleEffectsEnabled();
        this.saveGameData.soundEffectsEnabled = !this.saveGameData.soundEffectsEnabled;
      }).setOrigin(settingsLayout.originX, settingsLayout.originY))

    const closeButtonLayout = this.layoutData.ui.closeButton
    this.closeButton = new TextButton(
      this,
      closeButtonLayout.x,
      closeButtonLayout.y,
      this.buttonText,
      closeButtonLayout.bitmapFontId,
      closeButtonLayout.fontSize,
      closeButtonLayout.color,
      () => {
        writeSaveGameData()
        this.parent.destroy()
        this.scene.remove()
      }
    ).setOrigin(
      closeButtonLayout.originX,
      closeButtonLayout.originY
    )
    this.add.existing(this.closeButton)

    this.cameras.main.setBackgroundColor(0x000000)
    this.cameras.main.setViewport(this.parent.x, this.parent.y, 480, 320)

  }
}

export { showErrorModal }
export { showSettingsModal }
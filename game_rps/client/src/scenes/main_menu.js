import Phaser from 'phaser'

import { audioManager } from '../audio_manager.js'

// UI Widgets
import { TextButton } from '../ui_elements/text_button'
import { IconButton } from '../ui_elements/icon_button'
import { showErrorModal } from '../ui_elements/modals'
import { showSettingsModal } from '../ui_elements/modals'

// Gameplay
import { SinglePlayerGame } from '../game_engine_interface.js'

import { getSceneLayoutData } from '../game_data/layout.js'

import { getSaveGameData } from "../game_data/save_data"

class MainMenuScene extends Phaser.Scene {
  constructor () {
    super({ key: 'MainMenuScene' })
    this.menuHighlightIconIndex = 0
  }

  init (data) {
    this.error = data.error // This will be filled if returning from an error in another scene
    this.gameSaveData = getSaveGameData()
  }

  create () {
    this.layoutData = getSceneLayoutData('MainMenuScene')

    audioManager.initialize(this.game)
    audioManager.musicEnabled = this.gameSaveData.musicEnabled
    audioManager.effectsEnabled = this.gameSaveData.soundEffectsEnabled
    audioManager.playMusic('bgMusic', true)
    const bgLayout = this.layoutData.ui.background
    this.add.image(
      bgLayout.x, bgLayout.y, 'mainMenuBg'
    ).setOrigin(
      bgLayout.originX, bgLayout.originY
    )

    /**
      SINGLE PLAYER SELECT
    **/

    const menuButtonLayout = this.layoutData.ui.menu
    this.fistIndicator = this.add.sprite(
      menuButtonLayout.fistIndicatorX,
      menuButtonLayout.y + menuButtonLayout.fistIndicatorYOffset,
      'global_texture',
      'rock_ico'
    ).setRotation(
      1.5
    ).setTint(
      0xFF0000
    )

    const singlePlayerButton = new TextButton(
      this,
      menuButtonLayout.x,
      menuButtonLayout.y,
      'Single Player',
      menuButtonLayout.bitmapFontId,
      menuButtonLayout.fontSize,
      menuButtonLayout.color,
      () => { // On click
        console.log('Starting new single player game...')
        const gameInterface = new SinglePlayerGame({
          vsScreenDelay: 500
        },
        {
          sequence: 0,
          isBossFight: false,
          undefeated: true
        }
        )
        audioManager.playEffect('impact', {
          seek: 1
        })
        if (localStorage.getItem('skipIntroScene') === null) {
          this.scene.start('StoryIntroScene', { gameInterface: gameInterface })
        } else {
          this.scene.start('CharacterSelectScene', { gameInterface: gameInterface })
        }
      },
      () => { // On hover
        this.fistIndicator.setY(menuButtonLayout.y + menuButtonLayout.fistIndicatorYOffset)
        this.fistIndicator.setFrame(['rock_ico', 'paper_ico', 'scissors_ico'][++this.menuHighlightIconIndex % 3])
      }
    )
    singlePlayerButton.setOrigin(
      menuButtonLayout.originX,
      menuButtonLayout.originY
    )
    this.add.existing(singlePlayerButton)

    /**
      Multi Player Select
    **/
    if (window.getMatchmaker) { // only provide a multiplayer option is a Matchmaker is available
      const multiPlayerButtonYPos = menuButtonLayout.y + menuButtonLayout.padding + menuButtonLayout.fontSize
      const multiPlayerButton = new TextButton(this,
        menuButtonLayout.x,
        multiPlayerButtonYPos,
        'Multi Player',
        menuButtonLayout.bitmapFontId,
        menuButtonLayout.fontSize,
        menuButtonLayout.color,
        () => { // On click
          this.scene.start('MatchmakerScene')
        },
        () => { // On hover
          this.fistIndicator.setY(multiPlayerButtonYPos + menuButtonLayout.fistIndicatorYOffset)
          this.fistIndicator.setFrame(['rock_ico', 'paper_ico', 'scissors_ico'][++this.menuHighlightIconIndex % 3])
        }
      )
      multiPlayerButton.setOrigin(
        menuButtonLayout.originX,
        menuButtonLayout.originY
      )
      this.add.existing(multiPlayerButton)
    } else {
      console.log('No Matchmaker found - disabling multi player option.')
    }

    /**
      Settings Button
    **/

    const settingsButtonLayout = this.layoutData.ui.settingsButton
    const settingsButtonIcon = settingsButtonLayout.icons.settingsIcon
    this.add.existing(new IconButton(this,
      settingsButtonLayout.x, settingsButtonLayout.y, 'global_texture',
      settingsButtonIcon, settingsButtonIcon, 0xFFFFFF, () => {
      showSettingsModal(this)
      }).setOrigin(settingsButtonLayout.originX, settingsButtonLayout.originY))


    if (this.error) {
      showErrorModal(
        this,
        this.error.title,
        this.error.message,
        'Close'
      )
    }
  }
}

export { MainMenuScene }

import { describe, it, expect } from 'vitest'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'

const read = (path) => readFileSync(resolve(__dirname, '../..', path))
const html = read('index.html').toString()
const manifest = JSON.parse(read('public/manifest.webmanifest'))

// A PNG's width and height sit in its header
const pngSize = (path) => {
  const png = read(`public/${path}`)
  return [png.readUInt32BE(16), png.readUInt32BE(20)]
}

describe('Home Screen icons', () => {
  it('links the iOS icon and the manifest', () => {
    expect(html).toContain('<link rel="apple-touch-icon" href="/apple-touch-icon.png">')
    expect(html).toContain('<link rel="manifest" href="/manifest.webmanifest">')
    expect(html).toContain('<title>Chores</title>')
  })

  it('has an iOS icon of 180 by 180', () => {
    expect(pngSize('apple-touch-icon.png')).toEqual([180, 180])
  })

  it('lists icons of the sizes they say they are, with a maskable one', () => {
    for (const icon of manifest.icons) {
      const size = parseInt(icon.sizes)
      expect(pngSize(icon.src.slice(1))).toEqual([size, size])
    }
    expect(manifest.icons.some((icon) => icon.purpose?.includes('maskable'))).toBe(true)
  })
})

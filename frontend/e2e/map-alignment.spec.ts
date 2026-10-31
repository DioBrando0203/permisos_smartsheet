import { expect, test } from '@playwright/test'

test.beforeEach(async ({ page }) => {
  await page.route(/^https?:\/\/(?!127\.0\.0\.1[:/])/, (route) => route.abort())
})

test('desplaza la línea al eje y permite comparar el dibujo y la detección estricta', async ({ page }) => {
  await page.goto('/mapa?t=25.771778,-80.264110;25.782147,-80.264505')
  await expect(page.getByText(/Recorrido reconstruido sobre las vías/)).toBeVisible()
  await expect(page.locator('path.map-line--result')).toBeVisible()
  await expect(page.getByText('Inicio ajustado', { exact: true })).toBeVisible()
  await expect(page.locator('path.map-line--draft')).toHaveCount(0)
  await page.getByRole('checkbox', { name: 'Ver dibujo original' }).check()
  await expect(page.locator('path.map-line--draft')).toBeVisible()
  expect(new URL(page.url()).searchParams.get('original')).toBe('on')
  const strict = page.waitForRequest((request) => {
    const url = new URL(request.url())
    return url.pathname === '/api/map/trace' && url.searchParams.get('snap') === 'false'
  })
  await page.getByRole('checkbox', { name: 'Ajustar a vías (hasta 100 m)' }).uncheck()
  await strict
  await expect(page.getByText('Sin vías en el trazo')).toBeVisible()
  await expect(page.locator('path.map-line--result')).toHaveCount(0)
  expect(new URL(page.url()).searchParams.get('snap')).toBe('off')
})

test('dos puntos generan tres líneas siguiendo la red en vez de la diagonal dibujada', async ({ page }) => {
  await page.goto('/mapa?t=26.100000,-80.150000;26.104000,-80.146000')
  await expect(page.getByText(/Recorrido reconstruido sobre las vías/)).toBeVisible()
  const rows = page.getByRole('table').getByRole('row')
  await expect(rows).toHaveCount(4)
  await expect(rows.nth(1)).toContainText('SR 1001')
  await expect(rows.nth(2)).toContainText('SR 1002')
  await expect(rows.nth(3)).toContainText('SR 1003')
  await expect(page.locator('path.map-line--result')).toHaveCount(3)
  await expect(page.getByText(/Revisa cruces a desnivel/)).toBeVisible()
  await page.screenshot({ path: test.info().outputPath('recorrido-tres-vias.png'), fullPage: true })
})

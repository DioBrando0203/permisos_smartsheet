import { expect, test } from '@playwright/test'

// Backend real contra el GIS falso, que está en Miami-Dade: fuera de St. Johns la capa y el
// trazo dicen que no hay fuente del condado y el backend no consulta al condado (PEN-41).
test.beforeEach(async ({ page }) => {
  await page.route(/^https?:\/\/(?!127\.0\.0\.1[:/])/, (route) => route.abort())
})

test('la jurisdicción de calles pide celdas al acercarse y avisa fuera de St. Johns (CA-22)', async ({
  page,
}) => {
  // Incluye una recarga completa del mapa para la preferencia guardada.
  test.slow()
  await page.goto('/mapa?p=25.771778,-80.263610')
  const cells = page.waitForResponse(/\/api\/map\/streets\?west=/)
  await page.getByLabel('Jurisdicción de calles').check()
  expect((await cells).status()).toBe(200)
  await expect(page.getByText('Por ahora sólo St. Johns publica quién mantiene cada calle.')).toBeVisible()
  await page.reload()
  await expect(page.getByLabel('Jurisdicción de calles')).toBeChecked()
})

test('el trazo terminado tiene su sección de calles y permisos (CA-24)', async ({ page }) => {
  const streets = page.waitForResponse(/\/api\/map\/trace\/streets\?path=/)
  await page.goto('/mapa?t=25.771778,-80.263610;25.782147,-80.264005')
  expect((await streets).status()).toBe(200)
  const panel = page.getByRole('complementary', { name: 'Resultados del mapa' })
  const section = panel.getByRole('region', { name: 'Calles y permisos del trazo' })
  await expect(section).toContainText('Por ahora sólo St. Johns publica quién mantiene cada calle.')
  await expect(panel.getByRole('row').nth(1)).toContainText('SR 953')
})

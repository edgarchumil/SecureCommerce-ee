import { Navigate, Route, Routes } from 'react-router-dom'

import { HomePage } from '../pages/HomePage'
import { LoginPage } from '../pages/LoginPage'
import { NotFoundPage } from '../pages/NotFoundPage'
import { PanelPage } from '../pages/PanelPage'
import { SessionsPage } from '../pages/SessionsPage'
import { AssetsPage } from '../pages/AssetsPage'
import { AssetFormPage } from '../pages/AssetFormPage'
import { EvaluationCreatePage } from '../pages/EvaluationCreatePage'
import { EvaluationResultsPage } from '../pages/EvaluationResultsPage'
import { EvaluationsPage } from '../pages/EvaluationsPage'
import { QuestionnairePage } from '../pages/QuestionnairePage'
import { RisksPage } from '../pages/RisksPage'
import { RecommendationsPage } from '../pages/RecommendationsPage'
import { ReportsPage } from '../pages/ReportsPage'
import { AuditPage } from '../pages/AuditPage'
import { CompliancePage } from '../pages/CompliancePage'
import { IncidentsPage } from '../pages/IncidentsPage'
import { OrganizationPage } from '../pages/OrganizationPage'
import { PasswordResetPage } from '../pages/PasswordResetPage'
import { ProfilePage } from '../pages/ProfilePage'
import { SettingsPage } from '../pages/SettingsPage'
import { UsersPage } from '../pages/UsersPage'
import { RegisterPage } from '../pages/RegisterPage'
import { OrganizationsPage } from '../pages/OrganizationsPage'
import { PlatformPage } from '../pages/PlatformPage'
import { ProtectedRoute } from '../features/auth/ProtectedRoute'
import { AppShell } from '../components/AppShell'

export function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<HomePage />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/recuperar-contrasena" element={<PasswordResetPage />} />
      <Route path="/registro" element={<RegisterPage />} />
      <Route element={<ProtectedRoute />}>
        <Route element={<AppShell />}>
        <Route path="/panel" element={<PanelPage />} />
        <Route path="/sesiones" element={<SessionsPage />} />
        <Route path="/activos" element={<AssetsPage />} />
        <Route path="/activos/nuevo" element={<AssetFormPage />} />
        <Route path="/activos/:id/editar" element={<AssetFormPage />} />
        <Route path="/evaluaciones" element={<EvaluationsPage />} />
        <Route path="/evaluaciones/nueva" element={<EvaluationCreatePage />} />
        <Route path="/evaluaciones/:id/cuestionario" element={<QuestionnairePage />} />
        <Route path="/evaluaciones/:id/resultados" element={<EvaluationResultsPage />} />
        <Route path="/riesgos" element={<RisksPage />} />
        <Route path="/recomendaciones" element={<RecommendationsPage />} />
        <Route path="/reportes" element={<ReportsPage />} />
        <Route path="/organizacion" element={<OrganizationPage />} />
        <Route path="/usuarios" element={<UsersPage />} />
        <Route path="/auditoria" element={<AuditPage />} />
        <Route path="/perfil" element={<ProfilePage />} />
        <Route path="/configuracion" element={<SettingsPage />} />
        <Route path="/organizaciones" element={<OrganizationsPage />} />
        <Route path="/plataforma" element={<PlatformPage />} />
        <Route path="/cumplimiento" element={<CompliancePage />} />
        <Route path="/incidentes" element={<IncidentsPage />} />
        </Route>
      </Route>
      <Route path="/inicio" element={<Navigate replace to="/" />} />
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  )
}

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { UserPlus, Loader2, MoreHorizontal, KeyRound, Pencil, Trash2, ShieldCheck, User as UserIcon, Ban, CheckCircle2 } from "lucide-react";
import { toast } from "sonner";
import { api, apiError } from "@/lib/api";
import { formatDate } from "@/lib/format";
import { useAuth } from "@/features/auth/AuthContext";
import { PageHeader } from "@/components/PageHeader";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from "@/components/ui/dialog";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger, DropdownMenuSeparator } from "@/components/ui/dropdown-menu";
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle } from "@/components/ui/alert-dialog";

const roleLabel = (r) => (r === "admin" ? "Administrador" : "Técnico");
const emptyCreate = { email: "", name: "", role: "tecnico", password: "" };

export default function UsersPage() {
  const qc = useQueryClient();
  const { user: me } = useAuth();
  const [createOpen, setCreateOpen] = useState(false);
  const [createForm, setCreateForm] = useState(emptyCreate);
  const [editUser, setEditUser] = useState(null);
  const [pwUser, setPwUser] = useState(null);
  const [pwValue, setPwValue] = useState("");
  const [delUser, setDelUser] = useState(null);

  const { data: users = [], isLoading } = useQuery({
    queryKey: ["users"],
    queryFn: () => api.get("/auth/users").then((r) => r.data),
  });

  const invalidate = () => qc.invalidateQueries({ queryKey: ["users"] });

  const createMut = useMutation({
    mutationFn: (payload) => api.post("/auth/users", payload).then((r) => r.data),
    onSuccess: () => { invalidate(); setCreateOpen(false); setCreateForm(emptyCreate); toast.success("Usuario creado"); },
    onError: (e) => toast.error(apiError(e)),
  });
  const updateMut = useMutation({
    mutationFn: ({ id, patch }) => api.patch(`/auth/users/${id}`, patch).then((r) => r.data),
    onSuccess: () => { invalidate(); setEditUser(null); toast.success("Usuario actualizado"); },
    onError: (e) => toast.error(apiError(e)),
  });
  const pwMut = useMutation({
    mutationFn: ({ id, password }) => api.post(`/auth/users/${id}/reset-password`, { password }),
    onSuccess: () => { setPwUser(null); setPwValue(""); toast.success("Contraseña restablecida"); },
    onError: (e) => toast.error(apiError(e)),
  });
  const deleteMut = useMutation({
    mutationFn: (id) => api.delete(`/auth/users/${id}`),
    onSuccess: () => { invalidate(); setDelUser(null); toast.success("Usuario eliminado"); },
    onError: (e) => toast.error(apiError(e)),
  });

  const toggleActive = (u) => updateMut.mutate({ id: u.id, patch: { active: !u.active } });

  return (
    <div data-testid="users-page">
      <PageHeader
        label="Administración"
        title="Equipo"
        description="Gestiona las cuentas de los técnicos del despacho: altas, roles, acceso y contraseñas."
        actions={
          <Button className="rounded-sm" onClick={() => setCreateOpen(true)} data-testid="create-user-button">
            <UserPlus className="mr-2 h-4 w-4" /> Nuevo usuario
          </Button>
        }
      />

      {isLoading ? (
        <div className="flex justify-center py-16"><Loader2 className="h-6 w-6 animate-spin text-muted-foreground" /></div>
      ) : (
        <div className="border border-border bg-background" data-testid="users-table">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Nombre</TableHead><TableHead>Email</TableHead><TableHead>Rol</TableHead>
                <TableHead>Estado</TableHead><TableHead>Alta</TableHead><TableHead className="text-right">Acciones</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {users.map((u) => {
                const isSelf = u.id === me?.id;
                return (
                  <TableRow key={u.id} data-testid={`user-row-${u.id}`}>
                    <TableCell className="font-medium">{u.name}{isSelf && <span className="ml-2 text-xs text-muted-foreground">(tú)</span>}</TableCell>
                    <TableCell className="text-muted-foreground">{u.email}</TableCell>
                    <TableCell>
                      <Badge variant={u.role === "admin" ? "default" : "secondary"} className="rounded-sm">
                        {u.role === "admin" ? <ShieldCheck className="mr-1 h-3 w-3" /> : <UserIcon className="mr-1 h-3 w-3" />}
                        {roleLabel(u.role)}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline" className={`rounded-sm ${u.active ? "border-emerald-300 text-emerald-700" : "border-red-300 text-red-700"}`} data-testid={`user-${u.id}-status`}>
                        {u.active ? "Activo" : "Inactivo"}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-muted-foreground">{formatDate(u.created_at)}</TableCell>
                    <TableCell className="text-right">
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="icon" className="h-8 w-8" data-testid={`user-${u.id}-actions`}><MoreHorizontal className="h-4 w-4" /></Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem onClick={() => setEditUser({ ...u })} data-testid={`user-${u.id}-edit`}><Pencil className="mr-2 h-4 w-4" />Editar</DropdownMenuItem>
                          <DropdownMenuItem onClick={() => { setPwUser(u); setPwValue(""); }} data-testid={`user-${u.id}-reset`}><KeyRound className="mr-2 h-4 w-4" />Restablecer contraseña</DropdownMenuItem>
                          {!isSelf && (
                            <DropdownMenuItem onClick={() => toggleActive(u)} data-testid={`user-${u.id}-toggle`}>
                              {u.active ? <><Ban className="mr-2 h-4 w-4" />Desactivar</> : <><CheckCircle2 className="mr-2 h-4 w-4" />Activar</>}
                            </DropdownMenuItem>
                          )}
                          {!isSelf && <DropdownMenuSeparator />}
                          {!isSelf && <DropdownMenuItem className="text-destructive focus:text-destructive" onClick={() => setDelUser(u)} data-testid={`user-${u.id}-delete`}><Trash2 className="mr-2 h-4 w-4" />Eliminar</DropdownMenuItem>}
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </div>
      )}

      {/* Crear usuario */}
      <Dialog open={createOpen} onOpenChange={setCreateOpen}>
        <DialogContent data-testid="create-user-dialog">
          <DialogHeader><DialogTitle>Nuevo usuario</DialogTitle><DialogDescription>El usuario accederá con el email y la contraseña inicial que definas aquí.</DialogDescription></DialogHeader>
          <div className="space-y-4">
            <div><Label>Nombre</Label><Input className="mt-1" value={createForm.name} onChange={(e) => setCreateForm({ ...createForm, name: e.target.value })} data-testid="create-user-name" /></div>
            <div><Label>Email</Label><Input type="email" className="mt-1" value={createForm.email} onChange={(e) => setCreateForm({ ...createForm, email: e.target.value })} data-testid="create-user-email" /></div>
            <div><Label>Rol</Label>
              <Select value={createForm.role} onValueChange={(v) => setCreateForm({ ...createForm, role: v })}>
                <SelectTrigger className="mt-1" data-testid="create-user-role"><SelectValue /></SelectTrigger>
                <SelectContent><SelectItem value="tecnico">Técnico</SelectItem><SelectItem value="admin">Administrador</SelectItem></SelectContent>
              </Select>
            </div>
            <div><Label>Contraseña inicial</Label><Input type="text" className="mt-1 font-mono" placeholder="mínimo 6 caracteres" value={createForm.password} onChange={(e) => setCreateForm({ ...createForm, password: e.target.value })} data-testid="create-user-password" /></div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setCreateOpen(false)}>Cancelar</Button>
            <Button onClick={() => createMut.mutate(createForm)} disabled={createMut.isPending || !createForm.email || !createForm.name || createForm.password.length < 6} data-testid="create-user-submit">
              {createMut.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}Crear usuario
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Editar usuario */}
      <Dialog open={!!editUser} onOpenChange={(o) => !o && setEditUser(null)}>
        <DialogContent data-testid="edit-user-dialog">
          <DialogHeader><DialogTitle>Editar usuario</DialogTitle><DialogDescription>{editUser?.email}</DialogDescription></DialogHeader>
          {editUser && (
            <div className="space-y-4">
              <div><Label>Nombre</Label><Input className="mt-1" value={editUser.name} onChange={(e) => setEditUser({ ...editUser, name: e.target.value })} data-testid="edit-user-name" /></div>
              <div><Label>Rol</Label>
                <Select value={editUser.role} onValueChange={(v) => setEditUser({ ...editUser, role: v })} disabled={editUser.id === me?.id}>
                  <SelectTrigger className="mt-1" data-testid="edit-user-role"><SelectValue /></SelectTrigger>
                  <SelectContent><SelectItem value="tecnico">Técnico</SelectItem><SelectItem value="admin">Administrador</SelectItem></SelectContent>
                </Select>
                {editUser.id === me?.id && <p className="mt-1 text-xs text-muted-foreground">No puedes cambiar tu propio rol.</p>}
              </div>
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setEditUser(null)}>Cancelar</Button>
            <Button onClick={() => updateMut.mutate({ id: editUser.id, patch: { name: editUser.name, role: editUser.role } })} disabled={updateMut.isPending} data-testid="edit-user-submit">
              {updateMut.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}Guardar
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Restablecer contraseña */}
      <Dialog open={!!pwUser} onOpenChange={(o) => !o && setPwUser(null)}>
        <DialogContent data-testid="reset-pw-dialog">
          <DialogHeader><DialogTitle>Restablecer contraseña</DialogTitle><DialogDescription>Define una nueva contraseña para {pwUser?.name}. Comunícasela de forma segura.</DialogDescription></DialogHeader>
          <div><Label>Nueva contraseña</Label><Input type="text" className="mt-1 font-mono" placeholder="mínimo 6 caracteres" value={pwValue} onChange={(e) => setPwValue(e.target.value)} data-testid="reset-pw-value" /></div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setPwUser(null)}>Cancelar</Button>
            <Button onClick={() => pwMut.mutate({ id: pwUser.id, password: pwValue })} disabled={pwMut.isPending || pwValue.length < 6} data-testid="reset-pw-submit">
              {pwMut.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}Restablecer
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Eliminar */}
      <AlertDialog open={!!delUser} onOpenChange={(o) => !o && setDelUser(null)}>
        <AlertDialogContent data-testid="delete-user-dialog">
          <AlertDialogHeader><AlertDialogTitle>¿Eliminar a {delUser?.name}?</AlertDialogTitle><AlertDialogDescription>Se eliminará la cuenta de {delUser?.email}. Esta acción no se puede deshacer. Sus estudios seguirán existiendo.</AlertDialogDescription></AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancelar</AlertDialogCancel>
            <AlertDialogAction className="bg-destructive text-destructive-foreground hover:bg-destructive/90" onClick={() => deleteMut.mutate(delUser.id)} data-testid="delete-user-confirm">Eliminar</AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}

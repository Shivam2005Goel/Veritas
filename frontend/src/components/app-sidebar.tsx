"use client"

import { FileUp, ListTree, Repeat2, Search, Network } from "lucide-react"
import Link from "next/link"
import { usePathname } from "next/navigation"

import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from "@/components/ui/sidebar"

const items = [
  {
    title: "Ingestion Dashboard",
    url: "/",
    icon: FileUp,
  },
  {
    title: "Facts Explorer",
    url: "/facts",
    icon: ListTree,
  },
  {
    title: "Reconciliations",
    url: "/reconciliations",
    icon: Repeat2,
  },
  {
    title: "Fact Search & Q&A",
    url: "/search",
    icon: Search,
  },
  {
    title: "Dynamic Schema",
    url: "/schema",
    icon: Network,
  },
]

export function AppSidebar() {
  const pathname = usePathname()

  return (
    <Sidebar>
      <SidebarHeader className="p-4">
        <h2 className="text-xl font-bold tracking-tight text-primary">Veritas</h2>
        <p className="text-xs text-muted-foreground">Fact Knowledge Layer</p>
      </SidebarHeader>
      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupLabel>Navigation</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {items.map((item) => (
                <SidebarMenuItem key={item.title}>
                  <SidebarMenuButton isActive={pathname === item.url} render={<Link href={item.url} />}>
                    <item.icon />
                    <span>{item.title}</span>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>
    </Sidebar>
  )
}

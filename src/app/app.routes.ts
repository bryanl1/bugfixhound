import { Routes } from '@angular/router';
//import { HomeComponent } from './home/home.component';

export const routes: Routes = [
  { path: '', loadComponent: () => import('./app.component').then(m =>m.AppComponent) },        // Root route for front page
  { path: '**', redirectTo: '' },                // Fallback to front page
];

// import { NgModule } from '@angular/core';
// import { RouterModule, Routes } from '@angular/router';
// //import { HomeComponent } from './home/home.component';

// const routes: Routes = [
//   //{ path: '', component: HomeComponent },  // Front Page
//   { path: '**', redirectTo: '' }  // Catch-all route
// ];

// @NgModule({
//   imports: [RouterModule.forRoot(routes)],
//   exports: [RouterModule]
// })
// export class AppRoutingModule { }